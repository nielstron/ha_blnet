[![hacs_badge](https://img.shields.io/badge/HACS-Custom-orange.svg)](https://github.com/custom-components/hacs)

# BLNET custom component for Home Assistant

A custom component to integrate the freely pogrammable heating controller called [UVR1611 by Technische Alternative](https://www.ta.co.at/en/freely-programmable/uvr1611/)
into home assistant.

## Installation

Add this repository to [hacs](https://hacs.xyz/) or copy the `custom_component/blnet` file structure into your custom_component directory .

Afterwards, add these lines to your `configuration.yaml`:

      # UVR1611 Data
      blnet:
        resource: your_blnet_address
        password: optional_blnet_password
        can_node: optional_can_bus_node
        scan_interval: optional_scan_interval_seconds

Additional configuration options can be found in the `configurations.yaml` in [this repo](https://github.com/nielstron/ha-config).
There *is* the option to enable usage of the `ta_direct` protocal, which is however not properly working yet.

The result:

![Configured groups containing all available BLNet-supplied sensors](screenshot_blnet.png)

## A few notes

- Customization is fully supported.
- Grouping has to be manually accomplished.
- Digital outputs of the UVR1611 can be controlled via created switch entities.
- __Turning a switch off or on overrides the `AUTO` configuration and sets the switch to `HAND` until it is turned back to `AUTO` manually.__

## Contributions

Feel free to open Pull Requests here or at
the backend python script [pyblnet](https://github.com/nielstron/pyblnet).
