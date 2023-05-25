from harvesters.core import Harvester

from common import cti_file_path


def main():
    with Harvester() as h:
        print("Load .cti file...")
        h.add_file(str(cti_file_path), check_existence=True, check_validity=True)
        h.update()

        for item in h.device_info_list:
            print(
                f"{item.property_dict['serial_number']:<18}"
                f"{item.property_dict['model']:<25}"
                f"{item.property_dict['version']:<18}"
            )


if __name__ == "__main__":
    main()
