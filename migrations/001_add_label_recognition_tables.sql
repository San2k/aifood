-- Migration: Add label recognition tables
-- Created: 2026-02-28
-- Description: Tables for custom products, servings, and label scan tracking

-- Custom products created from nutrition labels
CREATE TABLE IF NOT EXISTS custom_products (
  id BIGSERIAL PRIMARY KEY,
  odentity VARCHAR(255) NOT NULL,
  product_name VARCHAR(500) NOT NULL,
  brand_name VARCHAR(255),
  barcode VARCHAR(100),

  -- Nutrition per 100g (always normalized to 100g)
  calories_per_100g NUMERIC(10, 2) NOT NULL,
  protein_per_100g NUMERIC(10, 2),
  carbs_per_100g NUMERIC(10, 2),
  fat_per_100g NUMERIC(10, 2),
  fiber_per_100g NUMERIC(10, 2),
  sugar_per_100g NUMERIC(10, 2),
  salt_per_100g NUMERIC(10, 2),
  sodium_per_100g NUMERIC(10, 2),

  -- Additional label data
  ingredients TEXT,
  allergens TEXT,

  -- Metadata
  source VARCHAR(50) DEFAULT 'label_scan' NOT NULL,
  created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
  updated_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
  is_deleted BOOLEAN DEFAULT FALSE NOT NULL,

  -- Constraints for data sanity
  CONSTRAINT check_calories_range CHECK (calories_per_100g >= 0 AND calories_per_100g <= 900),
  CONSTRAINT check_protein_range CHECK (protein_per_100g IS NULL OR (protein_per_100g >= 0 AND protein_per_100g <= 100)),
  CONSTRAINT check_carbs_range CHECK (carbs_per_100g IS NULL OR (carbs_per_100g >= 0 AND carbs_per_100g <= 100)),
  CONSTRAINT check_fat_range CHECK (fat_per_100g IS NULL OR (fat_per_100g >= 0 AND fat_per_100g <= 100)),
  CONSTRAINT check_fiber_range CHECK (fiber_per_100g IS NULL OR (fiber_per_100g >= 0 AND fiber_per_100g <= 50)),
  CONSTRAINT check_macros_sum CHECK (
    (COALESCE(protein_per_100g, 0) + COALESCE(carbs_per_100g, 0) + COALESCE(fat_per_100g, 0)) <= 120
  )
);

-- Indexes for custom_products
CREATE INDEX idx_custom_products_odentity ON custom_products(odentity) WHERE is_deleted = FALSE;
CREATE INDEX idx_custom_products_name ON custom_products(product_name) WHERE is_deleted = FALSE;
CREATE INDEX idx_custom_products_created_at ON custom_products(created_at DESC);

-- Serving sizes for custom products
CREATE TABLE IF NOT EXISTS servings (
  id BIGSERIAL PRIMARY KEY,
  product_id BIGINT NOT NULL REFERENCES custom_products(id) ON DELETE CASCADE,

  -- Serving definition
  serving_description VARCHAR(255) NOT NULL,
  serving_size_g NUMERIC(10, 2) NOT NULL,

  -- Optional serving equivalents
  serving_size_ml NUMERIC(10, 2),
  pieces_per_serving INTEGER,

  -- Is this the default/recommended serving?
  is_default BOOLEAN DEFAULT FALSE NOT NULL,

  created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,

  CONSTRAINT check_serving_size CHECK (serving_size_g > 0)
);

-- Indexes for servings
CREATE INDEX idx_servings_product_id ON servings(product_id);

-- Label scan tracking for confirmation workflow
CREATE TABLE IF NOT EXISTS label_scans (
  id BIGSERIAL PRIMARY KEY,
  scan_id VARCHAR(100) UNIQUE NOT NULL,
  odentity VARCHAR(255) NOT NULL,

  -- Input
  photo_url TEXT NOT NULL,
  photo_local_path TEXT,

  -- Processing metadata
  status VARCHAR(50) DEFAULT 'processing' NOT NULL,
  ocr_method VARCHAR(50),
  ocr_confidence NUMERIC(5, 4),
  markers_found TEXT[],

  -- Raw OCR data (for debugging)
  ocr_raw_text TEXT,
  ocr_structured_data JSONB,

  -- Extracted product data
  product_id BIGINT REFERENCES custom_products(id),

  -- User-provided overrides at confirmation
  user_edits JSONB,

  -- Error tracking
  error_message TEXT,
  retry_count INTEGER DEFAULT 0,

  -- Timestamps
  created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
  processed_at TIMESTAMPTZ,
  confirmed_at TIMESTAMPTZ,

  CONSTRAINT check_status_values CHECK (
    status IN ('processing', 'pending_confirmation', 'confirmed', 'cancelled', 'failed')
  ),
  CONSTRAINT check_ocr_confidence CHECK (
    ocr_confidence IS NULL OR (ocr_confidence >= 0 AND ocr_confidence <= 1)
  )
);

-- Indexes for label_scans
CREATE INDEX idx_label_scans_scan_id ON label_scans(scan_id);
CREATE INDEX idx_label_scans_odentity ON label_scans(odentity);
CREATE INDEX idx_label_scans_status ON label_scans(status) WHERE status IN ('processing', 'pending_confirmation');
CREATE INDEX idx_label_scans_created_at ON label_scans(created_at DESC);

-- Extend food_log_entry to reference custom products
ALTER TABLE food_log_entry
ADD COLUMN IF NOT EXISTS custom_product_id BIGINT REFERENCES custom_products(id);

CREATE INDEX IF NOT EXISTS idx_food_log_custom_product ON food_log_entry(custom_product_id);

-- Create trigger to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_custom_products_updated_at
BEFORE UPDATE ON custom_products
FOR EACH ROW
EXECUTE FUNCTION update_updated_at_column();

-- Comments for documentation
COMMENT ON TABLE custom_products IS 'User-created products from nutrition label scans';
COMMENT ON TABLE servings IS 'Serving size definitions for custom products';
COMMENT ON TABLE label_scans IS 'Tracks label processing workflow and confirmation status';

COMMENT ON COLUMN custom_products.calories_per_100g IS 'Always normalized to per 100g, range 0-900 kcal';
COMMENT ON COLUMN custom_products.source IS 'label_scan | manual | imported';
COMMENT ON COLUMN label_scans.status IS 'processing | pending_confirmation | confirmed | cancelled | failed';
COMMENT ON COLUMN label_scans.ocr_method IS 'paddleocr | gemini';
COMMENT ON COLUMN label_scans.ocr_confidence IS 'Global confidence score 0.0-1.0';
