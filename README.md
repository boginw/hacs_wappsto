<p align="center">
  <img src="https://wappsto.seluxit.com/wp-content/uploads/sites/2/2024/07/wappsto-by-wirtek.png" alt="Wappsto Logo" width="300"/>
</p>
<h1 align="center">Wappsto for Home Assistant</h1>

<p align="center">
  <a href="https://github.com/custom-components/hacs">
    <img src="https://img.shields.io/badge/HACS-Custom-41BDF5.svg" alt="HACS Custom">
  </a>
  <a href="https://github.com/Wappsto/hacs_wappsto/issues">
    <img src="https://img.shields.io/github/issues/Wappsto/hacs_wappsto" alt="GitHub Issues">
  </a>
</p>

Welcome to the official Wappsto integration for Home Assistant! This component allows you to seamlessly connect your
Home Assistant instance with the [Wappsto.com](https://wappsto.com) IoT platform, enabling you to both import Wappsto
devices into Home Assistant and export your Home Assistant entities to Wappsto.

## Features

* **Two-Way Sync**:
    * **Import**: Bring your Wappsto devices into Home Assistant to control them alongside your other smart home
      gadgets.
    * **Export**: Send your Home Assistant entities (like sensors, switches, and lights) to Wappsto to use them in
      Wappsto's dashboards and automation rules.
* **Simple Setup**: Get up and running in minutes with a straightforward configuration flow.
* **Real-Time Updates**: Uses websockets for instant communication between Home Assistant and Wappsto.
* **HACS Compatible**: Easily install and manage this integration with the Home Assistant Community Store (HACS).

## Prerequisites

Before you begin, you will need:

* A running instance of [Home Assistant](https://www.home-assistant.io/).
* [HACS (Home Assistant Community Store)](https://hacs.xyz/) installed.
* A free account on [Wappsto.com](https://wappsto.com).

---

## Installation

### 1. Add Custom Repository to HACS

* In Home Assistant, navigate to **HACS** > **Integrations**.
* Click the three dots (⋮) in the top-right corner and select **Custom repositories**.
* In the "Repository" field, enter:
  ```
  https://github.com/Wappsto/hacs_wappsto
  ```
* Select the **Integration** category.
* Click **Add**.

### 2. Install the Integration

* The Wappsto integration will now appear in your HACS integrations list.
* Click **Install** and proceed with the installation.
* HACS will prompt you to restart Home Assistant. **This is a required step.**

---

## Configuration

### 1. Add the Wappsto Integration

* After restarting, navigate to **Settings** > **Devices & Services**.
* Click the **+ ADD INTEGRATION** button in the bottom-right corner.
* Search for "Wappsto" and select it.
* Enter the email and password for your Wappsto.com account.

> **Note:** This step creates a secure network for your Home Assistant instance on Wappsto.com and adds a sensor to show
> its online status.

### 2. Configure Devices to Import/Export

Once the integration is added, you can decide what to sync.

* Navigate to the Wappsto integration under **Settings** > **Devices & Services**.
* Click **CONFIGURE**.
* You will see two options:
    * **Add devices from Wappsto**: Choose which of your Wappsto devices you want to import as entities in Home
      Assistant.
    * **Configure entities to export to Wappsto**: Choose which Home Assistant entities you want to send to your Wappsto
      network.

Entities are grouped by their device in Home Assistant. If an entity has no device, it will be placed under a "Default
device" in Wappsto.

## Contributing

Contributions are welcome! If you have an idea for a new feature, find a bug, or want to improve the documentation,
please feel free to open an issue or submit a pull request on
our [GitHub repository](https://github.com/Wappsto/hacs_wappsto).

## Support

If you encounter any issues or need help, please [open an issue](https://github.com/Wappsto/hacs_wappsto/issues) and
provide as much detail as possible, including logs and steps to reproduce the problem.
