# Device Registry - User Guide

## Overview

The device registry (`device_registry.yaml`) is a human-editable YAML file that stores custom names for your temperature monitoring devices. Names are automatically inferred when devices are first discovered, but you can easily customize them by editing the YAML file.

## File Location

```
config/device_registry.yaml
```

## How It Works

1. **Auto-Discovery**: When a device is first seen, the system automatically infers a readable name:
   - `Hall` + `hue_sensor` → `Hall Hue Sensor`
   - `Living Room` + `alexa_aqm` → `Living Room AQM`
   - `Hallway` + `nest_thermostat` → `Hallway Nest Thermostat`

2. **Auto-Registration**: The device is saved to `device_registry.yaml` with metadata:
   - `name`: Inferred or custom device name
   - `location`: Device location from config or API
   - `device_type`: Type of device (hue_sensor, alexa_aqm, nest_thermostat)
   - `model_info`: Device model (e.g., SML001, A3VRME03NAXFUB)
   - `first_seen`: First time device was discovered
   - `last_seen`: Last time device reported data

3. **Immediate Effect**: Changes to names in the YAML file take effect immediately on next collection

## Example Registry

```yaml
devices:
  hue:00:17:88:01:02:02:b5:21-02-0402:
    name: Kitchen Temperature Monitor
    location: Utility
    device_type: hue_sensor
    model_info: SML001
    first_seen: '2025-11-21 22:38:30'
    last_seen: '2025-11-21 22:39:04'
  
  alexa:GAJ23005314600H3:
    name: Living Room Air Quality
    location: Living Room
    device_type: amazon_aqm
    model_info: A3VRME03NAXFUB
    first_seen: '2025-11-21 22:38:40'
    last_seen: '2025-11-21 22:39:14'
```

## Customizing Device Names

### Method 1: Edit YAML File Directly (Recommended)

1. Open `config/device_registry.yaml` in any text editor
2. Find the device ID you want to rename
3. Change the `name` field to your preferred name
4. Save the file
5. Next collection will use the new name

**Example:**
```yaml
devices:
  hue:00:17:88:01:02:02:b5:21-02-0402:
    name: My Custom Sensor Name  # ← Edit this line
    location: Utility
    # ... rest unchanged
```

### Method 2: Programmatic Update

Use the device manager CLI (for advanced users):

```bash
# Using the YAML registry API
python3 -c "
from source.storage.yaml_device_registry import YAMLDeviceRegistry
reg = YAMLDeviceRegistry()
reg.set_device_name('hue:00:17:88:01:02:02:b5:21-02-0402', 'My New Name')
"
```

## Device ID Format

Device IDs follow a standard format:

- **Hue Sensors**: `hue:00:17:88:01:02:02:b5:21-02-0402`
  - Format: `hue:<zigbee_mac_address>-<endpoint>-<cluster>`

- **Amazon AQM**: `alexa:GAJ23005314600H3`
  - Format: `alexa:<device_serial>`

- **Nest Thermostats**: `nest:SKILL_<encoded_id>`
  - Format: `nest:<skill_appliance_id>`

## Best Practices

1. **Descriptive Names**: Use clear, descriptive names that identify both location and purpose
   - ✅ Good: `Kitchen Temperature Monitor`, `Bedroom Air Quality Sensor`
   - ❌ Avoid: `Sensor1`, `Device A`

2. **Consistent Naming**: Use consistent naming conventions across devices
   - Example: `[Location] [Type] [Purpose]`
   - `Living Room AQM`, `Hall Temperature Sensor`, `Kitchen Motion Sensor`

3. **Version Control**: The YAML file is plain text and works great with Git
   - Commit changes when you rename devices
   - Track history of device additions/removals

4. **Backup**: Keep a backup before making bulk changes
   ```bash
   cp config/device_registry.yaml config/device_registry.yaml.backup
   ```

## Viewing Devices

### List all registered devices:

```bash
python3 -c "
from source.storage.yaml_device_registry import YAMLDeviceRegistry
reg = YAMLDeviceRegistry()
devices = reg.list_devices()
for d in devices:
    print(f\"{d['unique_id']}: {d['name']}\")
"
```

### View raw YAML:

```bash
cat config/device_registry.yaml
```

## Troubleshooting

### Names not updating in database?

The registry controls what name is used for **new** readings. Existing readings in the database keep their original names. To update historical readings, you would need to run a database UPDATE query (not recommended unless necessary).

### Device not appearing in registry?

- Device must be discovered at least once
- Check that the collector ran successfully
- Verify device is online and reachable
- Check logs for any errors during collection

### YAML syntax errors?

- Ensure proper indentation (2 spaces, no tabs)
- Check for special characters in names (use quotes if needed)
- Validate YAML syntax: `python3 -c "import yaml; yaml.safe_load(open('config/device_registry.yaml'))"`

## Technical Details

- **File Format**: YAML (human-readable, version-control friendly)
- **Thread-Safe**: Uses file locking for concurrent access
- **No Database Dependency**: Names stored in filesystem, not SQLite
- **Auto-Creation**: File created automatically on first run
- **Metadata Tracking**: Timestamps track when devices were first/last seen

## Migration from Database Registry

If you were previously using the database-based device registry:

1. Old names in `device_registry` table are no longer used
2. YAML registry is now the source of truth
3. Devices will be auto-registered with inferred names on next collection
4. You can manually add devices to the YAML file if needed

## See Also

- `README.md` - Main project documentation
- `config/config.yaml` - Main configuration file
- `source/storage/yaml_device_registry.py` - Registry implementation
