-- Create audit database
CREATE DATABASE quickcart_audit;

-- Grant permissions
GRANT ALL PRIVILEGES ON DATABASE quickcart TO quickcart;
GRANT ALL PRIVILEGES ON DATABASE quickcart_audit TO quickcart;
