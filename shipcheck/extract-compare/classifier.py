"""Root shim re-exporting classifier components from core package."""
from core.classifier import *  # noqa: F401, F403
from core.classifier import EmailClassifier, ClassificationResult  # noqa: F401

if __name__ == "__main__":
    from core.classifier import main
    main()