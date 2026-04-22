"""
Supabase Storage Service
Handles file uploads and downloads for teacher notes and generated assignments
"""

import logging
import os
import re
from typing import BinaryIO, Optional, Dict, Any
from datetime import date
from app.database import supabase, supabase_admin

logger = logging.getLogger(__name__)

# Storage bucket names
TEACHER_NOTES_BUCKET = "teacher-notes"
ASSIGNMENTS_BUCKET = "assignments"
SUBMISSIONS_BUCKET = "submissions"


def sanitize_filename(filename: str) -> str:
    """Sanitize filename to remove problematic characters for Supabase Storage."""
    # Replace special characters with underscore
    sanitized = re.sub(r'[^a-zA-Z0-9._-]', '_', filename)
    # Remove multiple underscores
    sanitized = re.sub(r'_+', '_', sanitized)
    # Remove leading/trailing underscores
    sanitized = sanitized.strip('_')
    return sanitized


class StorageService:
    """Service for managing files in Supabase Storage."""
    
    @staticmethod
    def ensure_buckets_exist():
        """Check and optionally create storage buckets. Buckets can be created manually via Supabase."""
        logger.info("📦 Checking storage buckets...")
        
        buckets_to_check = [
            (TEACHER_NOTES_BUCKET, "Teacher notes and reference materials"),
            (ASSIGNMENTS_BUCKET, "Generated assignment PDFs"),
            (SUBMISSIONS_BUCKET, "Student submission files")
        ]
        
        missing_buckets = []
        
        for bucket_name, description in buckets_to_check:
            try:
                supabase.storage.get_bucket(bucket_name)
                logger.info(f"✓ Bucket exists: {bucket_name}")
            except Exception as e:
                logger.warning(f"⚠️  Bucket not found: {bucket_name} ({description})")
                missing_buckets.append((bucket_name, description))
                
                # Try to create it, but don't fail if permission denied
                try:
                    logger.info(f"  Attempting to create bucket: {bucket_name}")
                    supabase.storage.create_bucket(
                        id=bucket_name,
                        options={"public": False}
                    )
                    logger.info(f"  ✓ Bucket created: {bucket_name}")
                except Exception as create_err:
                    logger.warning(f"  ⚠️  Could not auto-create bucket (permission denied): {bucket_name}")
                    logger.warning(f"  → Create manually via Supabase dashboard: Storage → New Bucket")
        
        if missing_buckets:
            logger.warning("\n" + "="*60)
            logger.warning("⚠️  MISSING STORAGE BUCKETS - CREATE MANUALLY:")
            logger.warning("="*60)
            for bucket_name, description in missing_buckets:
                logger.warning(f"  • {bucket_name}: {description}")
            logger.warning("\nSteps:")
            logger.warning("  1. Go to Supabase Dashboard → Storage")
            logger.warning("  2. Click 'New Bucket' for each bucket above")
            logger.warning("  3. Set 'Public' to OFF (Private buckets)")
            logger.warning("="*60 + "\n")
        else:
            logger.info("✅ All buckets ready")
    
    @staticmethod
    def upload_teacher_notes(
        file_path: str,
        user_id: str,
        subject: str,
        assignment_no: str
    ) -> Dict[str, Any]:
        """
        Upload teacher notes/reference material to Supabase Storage.
        Uses service role key to bypass RLS policies.
        
        Args:
            file_path: Path to the file to upload
            user_id: UUID of the faculty member
            subject: Subject name
            assignment_no: Assignment number
        
        Returns:
            Dict with file_path and download_url
        
        Raises:
            Exception: If upload fails
        """
        try:
            logger.info(f"📤 Uploading teacher notes: {file_path}")
            
            # Validate service role client
            if not supabase_admin:
                logger.error("❌ SERVICE_ROLE_KEY not configured! Upload will use anon key and may fail.")
                logger.error("   Add SUPABASE_SERVICE_KEY to .env file")
                raise ValueError("SERVICE_ROLE_KEY not configured in .env")
            
            # Read file
            with open(file_path, "rb") as f:
                file_content = f.read()
            
            logger.info(f"   ✓ File read: {len(file_content)} bytes")
            
            # Generate storage path
            file_name = os.path.basename(file_path)
            storage_path = f"{user_id}/{subject}/assignment-{assignment_no}/{file_name}"
            
            logger.info(f"   📁 Storing at: {storage_path}")
            
            # Upload to Supabase Storage using service role (bypasses RLS)
            logger.info(f"   📤 Uploading to {TEACHER_NOTES_BUCKET} bucket (using service role)...")
            response = supabase_admin.storage.from_(TEACHER_NOTES_BUCKET).upload(
                storage_path,
                file_content,
                file_options={"content-type": "application/pdf"}
            )
            
            logger.info(f"✅ File uploaded successfully: {storage_path}")
            
            # Get public URL (using anon client is fine for URLs)
            url = supabase.storage.from_(TEACHER_NOTES_BUCKET).get_public_url(storage_path)
            logger.info(f"   🔗 Public URL: {url[:60]}...")
            
            return {
                "status": "success",
                "file_path": storage_path,
                "storage_url": url,
                "bucket": TEACHER_NOTES_BUCKET,
                "size": len(file_content)
            }
            
        except Exception as e:
            logger.error(f"❌ Teacher notes upload failed: {str(e)}")
            logger.error(f"   Error type: {type(e).__name__}")
            logger.error(f"   Check: Is SERVICE_ROLE_KEY configured in .env?")
            raise
    
    @staticmethod
    def upload_assignment_pdf(
        file_path: str,
        user_id: str,
        subject: str,
        assignment_no: str,
        semester: str
    ) -> Dict[str, Any]:
        """
        Upload generated assignment PDF to Supabase Storage.
        Uses service role key to bypass RLS policies.
        
        Args:
            file_path: Path to the PDF file
            user_id: UUID of the faculty member
            subject: Subject name
            assignment_no: Assignment number
            semester: Semester
        
        Returns:
            Dict with file_path and download_url
        
        Raises:
            Exception: If upload fails
        """
        try:
            logger.info(f"📤 Uploading assignment PDF: {file_path}")
            
            # Validate service role client
            if not supabase_admin:
                logger.error("❌ SERVICE_ROLE_KEY not configured! Upload will use anon key and may fail.")
                logger.error("   Add SUPABASE_SERVICE_KEY to .env file")
                raise ValueError("SERVICE_ROLE_KEY not configured in .env")
            
            # Read file
            with open(file_path, "rb") as f:
                file_content = f.read()
            
            logger.info(f"   ✓ File read: {len(file_content)} bytes")
            
            # Generate storage path
            file_name = os.path.basename(file_path)
            storage_path = f"{user_id}/{subject}/semester-{semester}/assignment-{assignment_no}/{file_name}"
            
            logger.info(f"   📁 Storing at: {storage_path}")
            
            # Upload to Supabase Storage using service role (bypasses RLS)
            logger.info(f"   📤 Uploading to {ASSIGNMENTS_BUCKET} bucket (using service role)...")
            response = supabase_admin.storage.from_(ASSIGNMENTS_BUCKET).upload(
                storage_path,
                file_content,
                file_options={"content-type": "application/pdf"}
            )
            
            logger.info(f"✅ Assignment PDF uploaded successfully: {storage_path}")
            
            # Get public URL (using anon client is fine for URLs)
            url = supabase.storage.from_(ASSIGNMENTS_BUCKET).get_public_url(storage_path)
            logger.info(f"   🔗 Public URL: {url[:60]}...")
            
            return {
                "status": "success",
                "file_path": storage_path,
                "storage_url": url,
                "bucket": ASSIGNMENTS_BUCKET,
                "size": len(file_content)
            }
            
        except Exception as e:
            logger.error(f"❌ Assignment PDF upload failed: {str(e)}")
            logger.error(f"   Error type: {type(e).__name__}")
            logger.error(f"   Check: Is SERVICE_ROLE_KEY configured in .env?")
            raise
    
    @staticmethod
    def download_file(bucket: str, file_path: str) -> BinaryIO:
        """
        Download file from Supabase Storage.
        
        Args:
            bucket: Bucket name
            file_path: Path to file in storage
        
        Returns:
            File content as bytes
        """
        try:
            logger.info(f"📥 Downloading from {bucket}: {file_path}")
            
            response = supabase.storage.from_(bucket).download(file_path)
            
            logger.info("✓ File downloaded")
            return response
            
        except Exception as e:
            logger.error(f"❌ Download failed: {str(e)}")
            raise
    
    @staticmethod
    def get_public_url(bucket: str, file_path: str) -> str:
        """
        Get public URL for a file in Supabase Storage.
        
        Args:
            bucket: Bucket name
            file_path: Path to file in storage
        
        Returns:
            Public URL string
        """
        try:
            url = supabase.storage.from_(bucket).get_public_url(file_path)
            logger.info(f"✓ Generated URL: {url}")
            return url
            
        except Exception as e:
            logger.error(f"❌ Error generating URL: {str(e)}")
            raise
    
    @staticmethod
    def list_files(bucket: str, prefix: str = "") -> list:
        """
        List all files in a bucket (optionally with prefix).
        
        Args:
            bucket: Bucket name
            prefix: Optional prefix to filter files
        
        Returns:
            List of file info dicts
        """
        try:
            logger.info(f"📂 Listing files in {bucket} (prefix: {prefix})")
            
            files = supabase.storage.from_(bucket).list(prefix)
            
            logger.info(f"✓ Found {len(files)} files")
            return files
            
        except Exception as e:
            logger.error(f"❌ Error listing files: {str(e)}")
            raise
    
    @staticmethod
    def delete_file(bucket: str, file_path: str) -> bool:
        """
        Delete a file from Supabase Storage.
        
        Args:
            bucket: Bucket name
            file_path: Path to file in storage
        
        Returns:
            True if successful
        """
        try:
            logger.info(f"🗑️ Deleting from {bucket}: {file_path}")
            
            supabase.storage.from_(bucket).remove([file_path])
            
            logger.info("✓ File deleted")
            return True
            
        except Exception as e:
            logger.error(f"❌ Delete failed: {str(e)}")
            raise
    
    @staticmethod
    def upload_file_to_submissions(
        file_path: str,
        assignment_id: str,
        student_id: str,
        file_name: str
    ) -> Dict[str, Any]:
        """
        Upload student submission file to Supabase Storage.
        Uses admin client (service role) to bypass storage RLS policies.
        
        Args:
            file_path: Path to the file to upload
            assignment_id: UUID of the assignment
            student_id: UUID of the student
            file_name: Name of the file
        
        Returns:
            Dict with file_path and download_url
        
        Raises:
            Exception: If upload fails
        """
        try:
            logger.info(f"📤 Uploading student submission: {file_path}")
            
            # Verify file exists and get size
            if not os.path.exists(file_path):
                raise FileNotFoundError(f"File not found: {file_path}")
            
            file_size = os.path.getsize(file_path)
            logger.info(f"   File size: {file_size} bytes")
            
            # Sanitize filename
            safe_filename = sanitize_filename(file_name)
            logger.info(f"   Original filename: {file_name} → Safe filename: {safe_filename}")
            
            # Read file
            try:
                with open(file_path, "rb") as f:
                    file_content = f.read()
                logger.info(f"   ✓ File read successfully")
            except Exception as e:
                logger.error(f"   ❌ Failed to read file: {str(e)}")
                raise
            
            # Generate storage path
            storage_path = f"{assignment_id}/{student_id}/{safe_filename}"
            
            logger.info(f"   Storing at: {storage_path}")
            
            # Upload to Supabase Storage
            try:
                logger.info(f"   🚀 Starting upload to Supabase...")
                # Use admin client to bypass storage RLS policies
                storage_client = supabase_admin if supabase_admin else supabase
                response = storage_client.storage.from_(SUBMISSIONS_BUCKET).upload(
                    storage_path,
                    file_content,
                    file_options={"content-type": "application/pdf"}
                )
                logger.info(f"   ✓ Upload response received")
            except Exception as upload_error:
                logger.error(f"   ❌ Upload error: {str(upload_error)}")
                raise Exception(f"Supabase storage upload failed: {str(upload_error)}")
            
            logger.info(f"✓ Submission uploaded: {storage_path}")
            
            # Get public URL
            try:
                url = supabase.storage.from_(SUBMISSIONS_BUCKET).get_public_url(storage_path)
                logger.info(f"   ✓ Public URL obtained")
            except Exception as url_error:
                logger.warning(f"   ⚠️ Could not get public URL: {str(url_error)}")
                url = f"https://{supabase.storage.url}/object/public/{SUBMISSIONS_BUCKET}/{storage_path}"
            
            return {
                "status": "success",
                "file_path": storage_path,
                "storage_url": url,
                "bucket": SUBMISSIONS_BUCKET,
                "size": len(file_content)
            }
            
        except Exception as e:
            logger.error(f"❌ Submission upload failed: {str(e)}", exc_info=True)
            raise
