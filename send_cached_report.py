"""send_cached_report.py

Sends the cached daily report via email.

This script reads the cached email content from 'models/email_cache.json'
and sends it using the configured SMTP settings.

Usage: 
    python send_cached_report.py                    # Send the latest cached report
    python send_cached_report.py --preview          # Preview email content without sending
    python send_cached_report.py --cache <path>     # Send from a specific cache file

Examples:
    python send_cached_report.py
    python send_cached_report.py --preview
    python send_cached_report.py --cache models/email_cache_backup.json
"""
import os
import sys
import json
import argparse
from datetime import datetime

from src.email_sender import send_email_report

# Configuration constants
MODELS_DIR = 'models'
EMAIL_CONFIG = 'email_config.json'
DEFAULT_CACHE_PATH = os.path.join(MODELS_DIR, 'email_cache.json')


def load_email_cache(cache_path: str) -> dict:
    """
    Load email cache from JSON file.
    
    Args:
        cache_path: Path to the cache JSON file
        
    Returns:
        Dictionary containing email content and metadata
        
    Raises:
        FileNotFoundError: If cache file doesn't exist
        json.JSONDecodeError: If cache file is not valid JSON
    """
    if not os.path.exists(cache_path):
        raise FileNotFoundError(f"Cache file not found: {cache_path}")
    
    with open(cache_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def preview_email(cache: dict) -> None:
    """
    Display email content preview.
    
    Args:
        cache: Email cache dictionary
    """
    print("\n" + "="*80)
    print("📧 EMAIL PREVIEW")
    print("="*80)
    print(f"\n📅 Generated: {cache.get('generated_at', 'N/A')}")
    print(f"📆 Date: {cache.get('date', 'N/A')}")
    print(f"\n📌 Subject: {cache.get('subject', 'N/A')}")
    print("\n" + "-"*80)
    print("📝 Body:")
    print("-"*80)
    print(cache.get('body', 'N/A'))
    print("\n" + "-"*80)
    print("📎 Attachments:")
    print("-"*80)
    
    attachments = cache.get('attachments', [])
    if attachments:
        for i, attachment in enumerate(attachments, 1):
            exists = "✓" if os.path.exists(attachment) else "✗"
            print(f"  {i}. {exists} {attachment}")
    else:
        print("  No attachments")
    
    print("\n" + "="*80)


def verify_attachments(attachments: list) -> tuple:
    """
    Verify that all attachment files exist.
    
    Args:
        attachments: List of attachment file paths
        
    Returns:
        Tuple of (all_exist: bool, missing_files: list)
    """
    missing = []
    for attachment in attachments:
        if not os.path.exists(attachment):
            missing.append(attachment)
    
    return len(missing) == 0, missing


def send_cached_email(cache_path: str, email_config_path: str, to_addresses: list = None) -> bool:
    """
    Send email using cached content.
    
    Args:
        cache_path: Path to the email cache file
        email_config_path: Path to the email configuration file
        to_addresses: Optional list of recipient email addresses (overrides config)
        
    Returns:
        True if email sent successfully, False otherwise
    """
    try:
        # Load cache
        print(f"Loading email cache from: {cache_path}")
        cache = load_email_cache(cache_path)
        
        # Extract email components
        subject = cache.get('subject', 'BUFF Market AI Analysis Report')
        body = cache.get('body', 'AI analysis summary not available.')
        attachments = cache.get('attachments', [])
        
        # Verify attachments
        all_exist, missing = verify_attachments(attachments)
        if not all_exist:
            print("\n⚠️  Warning: Some attachment files are missing:")
            for missing_file in missing:
                print(f"  ✗ {missing_file}")
            
            response = input("\nContinue sending without missing files? (y/N): ")
            if response.lower() != 'y':
                print("Email sending cancelled.")
                return False
            
            # Filter out missing files
            attachments = [a for a in attachments if os.path.exists(a)]
        
        # Send email
        if to_addresses:
            print(f"\n📧 Sending email to {len(to_addresses)} custom recipient(s)...")
            for addr in to_addresses:
                print(f"  → {addr}")
        else:
            print("\n📧 Sending email to recipients from config file...")
        
        success = send_email_report(
            email_config_path=email_config_path,
            subject=subject,
            body=body,
            attachments=attachments,
            to_addresses=to_addresses
        )
        
        if success:
            print("\n✅ Email sent successfully!")
            
            # Update cache with send timestamp
            cache['last_sent_at'] = datetime.now().isoformat()
            with open(cache_path, 'w', encoding='utf-8') as f:
                json.dump(cache, f, ensure_ascii=False, indent=2)
            
            return True
        else:
            print("\n❌ Failed to send email. Check email configuration and try again.")
            return False
            
    except FileNotFoundError as e:
        print(f"\n❌ Error: {e}")
        print("Please run 'python run_daily_report.py' first to generate the report.")
        return False
    except json.JSONDecodeError as e:
        print(f"\n❌ Error: Invalid cache file format: {e}")
        return False
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        return False


def main():
    """Main function."""
    parser = argparse.ArgumentParser(
        description='Send cached daily report via email',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python send_cached_report.py                         # Send latest cached report
  python send_cached_report.py --preview               # Preview without sending
  python send_cached_report.py --cache models/old.json # Send from specific cache
        """
    )
    
    parser.add_argument(
        '--cache',
        default=DEFAULT_CACHE_PATH,
        help=f'Path to email cache file (default: {DEFAULT_CACHE_PATH})'
    )
    
    parser.add_argument(
        '--preview',
        action='store_true',
        help='Preview email content without sending'
    )
    
    parser.add_argument(
        '--email-config',
        default=EMAIL_CONFIG,
        help=f'Path to email config file (default: {EMAIL_CONFIG})'
    )
    
    parser.add_argument(
        '--to',
        nargs='+',
        help='Recipient email addresses (overrides config file). Can specify multiple: --to email1@example.com email2@example.com'
    )
    
    args = parser.parse_args()
    
    try:
        # Load cache
        cache = load_email_cache(args.cache)
        
        if args.preview:
            # Preview mode
            preview_email(cache)
            print("\n💡 To send this email, run without --preview flag")
        else:
            # Send mode
            preview_email(cache)
            
            response = input("\n❓ Send this email? (y/N): ")
            if response.lower() == 'y':
                send_cached_email(args.cache, args.email_config, args.to)
            else:
                print("Email sending cancelled.")
                
    except FileNotFoundError as e:
        print(f"\n❌ Error: {e}")
        print("\n💡 Please run 'python run_daily_report.py' first to generate the report.")
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"\n❌ Error: Invalid cache file format: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()
