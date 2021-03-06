variable "name" {
  description = "Prefix name for GCS bucket"
  type        = string
}

variable "location" {
  description = "Location for gcs bucket"
  type        = string
}

variable "versioning" {
  description = "Enable versioning on bucket"
  type        = bool
  default     = true
}

variable "public" {
  description = "Google Cloud Storage s3 bucket is exposed publicly (currently ignored)"
  type        = bool
  default     = false
}
