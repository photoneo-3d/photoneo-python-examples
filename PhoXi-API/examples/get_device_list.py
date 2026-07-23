import pprint
import sys

from phoxi_api import PhoXiControl

if __name__ == "__main__":
    phoxi_control = PhoXiControl()
    if not phoxi_control.is_phoxicontrol_running():
        print("PhoXi Control is not running. Please start PhoXi Control and try again.")
        sys.exit(1)

    # Pass refresh=True to force refresh of device discovery,
    # but then this call will take few seconds to complete
    device_list = phoxi_control.get_device_list(refresh=False)

    print(f"Found {len(device_list)} devices:")
    pprint.pp(device_list)
