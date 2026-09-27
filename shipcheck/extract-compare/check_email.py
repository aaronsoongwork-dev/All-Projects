"""Root shim re-exporting check_email components from core package."""
from core.check_email import *  # noqa: F401, F403
from core.check_email import (  # noqa: F401
    EmailMessage,
    AttachmentExtractor,
    EmailVerificationPipeline,
    VerificationReport,
    ConsoleReporter,
    EmailCheckerApp,
    normalize_id,
    load_email,
    get_fields_for_attachment,
    main,
)

if __name__ == "__main__":
    main()