"""Root shim re-exporting extract components from core package."""
from core.extract import *  # noqa: F401, F403
from core.extract import (  # noqa: F401
    extract_fields,
    extract_fields_from_image,
    FIELDS,
)

if __name__ == "__main__":
    sample = """
    SHIPPING INSTRUCTION
    Shipper: APRIL FAR EAST (M) SDN BHD
    Consignee (Non-Negotiable): EAST BRIGHT FZ-LLC
    Notify: EAST BRIGHT FZ-LLC
    Port of Loading (POL): NANTONG, CHINA (CNNTG)
    POD: KARACHI, PAKISTAN (PKKHI)
    Total Containers: 6 x 40'HC
    Gross Wt (kgs): 131,058 KG
    """
    print(extract_fields(sample))
