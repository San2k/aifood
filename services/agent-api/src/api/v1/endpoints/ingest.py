"""
/v1/ingest endpoint - main entry point for processing user messages.
"""

import logging
from fastapi import APIRouter, HTTPException
from typing import Dict, Any
import uuid
from datetime import datetime, timedelta

from ..schemas.ingest import IngestRequest, IngestResponse, ClarificationRequest as ClarificationSchema
from ....graph.state import create_initial_state
from ....graph.graph import nutrition_graph
from ....db.session import AsyncSessionLocal
from ....db.repositories.user_repository import UserRepository
from ....db.repositories.conversation_repository import ConversationRepository

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/ingest", response_model=IngestResponse)
async def ingest_message(request: IngestRequest) -> IngestResponse:
    """
    Process user message through nutrition bot graph.
    
    Main endpoint that:
    1. Creates initial state from request
    2. Executes LangGraph
    3. Returns response with results or clarification requests
    
    Args:
        request: Ingest request with user message
        
    Returns:
        IngestResponse with results or clarification requests
    """
    logger.info(f"Processing message from telegram_id {request.telegram_id}: {request.message[:50]}...")

    try:
        # Get or create user in database
        async with AsyncSessionLocal() as session:
            user_repo = UserRepository(session)
            user, created = await user_repo.get_or_create_user(
                telegram_id=request.telegram_id,
                username=request.username,
                first_name=request.first_name,
                last_name=request.last_name
            )
            await session.commit()

            db_user_id = user.id

        if created:
            logger.info(f"Created new user: telegram_id={request.telegram_id}, user_id={db_user_id}")
        else:
            logger.info(f"Found existing user: telegram_id={request.telegram_id}, user_id={db_user_id}")

        # Generate conversation ID if not provided
        conversation_id = request.conversation_id or str(uuid.uuid4())

        # Check if we're resuming a conversation with clarification responses
        initial_state = None
        if request.clarification_responses and request.conversation_id:
            # Try to load previous conversation state
            async with AsyncSessionLocal() as session:
                conv_repo = ConversationRepository(session)
                previous_state = await conv_repo.get_conversation_state(conversation_id)

                if previous_state:
                    logger.info(f"Loaded previous state for conversation {conversation_id}")
                    # Merge clarification responses into previous state
                    initial_state = previous_state.copy()
                    initial_state["clarification_responses"] = request.clarification_responses
                    initial_state["raw_input"] = request.message
                    initial_state["message_id"] = request.message_id
                    initial_state["updated_at"] = datetime.utcnow()
                    # Skip input detection and normalization - go directly to clarification processing
                    initial_state["next_node"] = "need_clarification"
                    initial_state["should_end"] = False

        # Create fresh state if not resuming
        if not initial_state:
            initial_state = create_initial_state(
                user_id=db_user_id,
                telegram_id=request.telegram_id,
                conversation_id=conversation_id,
                input_type=request.input_type,
                raw_input=request.message,
                message_id=request.message_id,
                photo_file_id=request.photo_file_id,
                clarification_responses=request.clarification_responses
            )
        
        # Execute graph
        logger.info(f"Executing graph for conversation {conversation_id}")
        final_state = await nutrition_graph.ainvoke(initial_state)
        
        logger.info(f"Graph execution completed. State keys: {list(final_state.keys())}")
        
        # Save conversation state if waiting for clarification
        needs_clarification = final_state.get("needs_clarification", False)
        if needs_clarification:
            async with AsyncSessionLocal() as session:
                conv_repo = ConversationRepository(session)
                current_node = final_state.get("next_node", "need_clarification")
                # Expire after 1 hour
                expires_at = datetime.utcnow() + timedelta(hours=1)
                await conv_repo.save_conversation_state(
                    user_id=db_user_id,
                    conversation_id=conversation_id,
                    current_node=current_node,
                    graph_state=final_state,
                    expires_at=expires_at
                )
                logger.info(f"Saved conversation state for {conversation_id}")
        else:
            # Conversation completed, deactivate state
            async with AsyncSessionLocal() as session:
                conv_repo = ConversationRepository(session)
                await conv_repo.deactivate_conversation(conversation_id)
                logger.info(f"Deactivated completed conversation {conversation_id}")
        
        # Build response
        clarification_requests = final_state.get("clarification_requests", [])
        saved_entry_ids = final_state.get("saved_entry_ids", [])
        daily_totals = final_state.get("daily_totals")
        ai_advice = final_state.get("ai_advice")
        errors = final_state.get("errors", [])
        
        # Generate reply text
        reply_text = None
        
        if needs_clarification and clarification_requests:
            # Return clarification questions
            clarif = clarification_requests[0]
            reply_text = clarif.get("question", "Уточните, пожалуйста")
        
        elif saved_entry_ids and daily_totals:
            # Success - show results
            calories = daily_totals.get("calories", 0)
            protein = daily_totals.get("protein", 0)
            carbs = daily_totals.get("carbohydrates", 0)
            fat = daily_totals.get("fat", 0)

            reply_text = f"✅ Сохранено!\n\n"
            reply_text += f"📊 Итого за сегодня:\n"
            reply_text += f"Калории: {calories:.0f} ккал\n"
            reply_text += f"Белки: {protein:.1f}г\n"
            reply_text += f"Углеводы: {carbs:.1f}г\n"
            reply_text += f"Жиры: {fat:.1f}г"

            if ai_advice:
                reply_text += f"\n\n💡 {ai_advice}"

        elif ai_advice:
            # Conversational response (questions, greetings, report requests)
            reply_text = ai_advice

        elif errors:
            reply_text = f"❌ Ошибка: {errors[0]}"
        
        # Convert clarification requests to schemas
        clarif_schemas = [
            ClarificationSchema(
                type=c.get("type", "unknown"),
                question=c.get("question", ""),
                options=c.get("options"),
                context=c.get("context", {})
            )
            for c in clarification_requests
        ]
        
        response = IngestResponse(
            success=len(errors) == 0,
            conversation_id=conversation_id,
            reply_text=reply_text,
            needs_clarification=needs_clarification,
            clarification_requests=clarif_schemas,
            saved_entries=saved_entry_ids,
            daily_totals=daily_totals,
            ai_advice=ai_advice,
            errors=errors
        )
        
        logger.info(f"Returning response: success={response.success}, needs_clarification={response.needs_clarification}")
        return response
        
    except Exception as e:
        logger.error(f"Error processing message: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}"
        )
