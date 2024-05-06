#!/usr/bin/env python3
from harvesters.core import Harvester

from gentl_producer_loader import producer_path


def main():
    with Harvester() as h:
        h.add_file(str(producer_path), check_existence=True, check_validity=True)
        h.update()

        print(
            f"{'Serial number':<25}{'Model':<25}{'Vendor':<25}{'Display name':<55}{'User defined name':<25}"
        )
        print("*" * 155)
        for item in h.device_info_list:
            print(
                f"{item.property_dict['serial_number']:<25}"
                f"{item.property_dict['model']:<25}"
                f"{item.property_dict['vendor']:<25}"
                f"{item.property_dict['display_name']:<55}"
                f"{item.property_dict['user_defined_name']:<25}"
            )


if __name__ == "__main__":
    main()
