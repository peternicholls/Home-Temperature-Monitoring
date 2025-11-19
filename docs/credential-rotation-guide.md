# Credential Rotation Guide

## Philips Hue API Key Rotation

### Security Assessment (2025-11-19)

✅ **Status**: No credentials leaked in git history
- `config/secrets.yaml` is properly in `.gitignore`
- No commits contain actual API keys
- Repository only contains template files

### When to Rotate Credentials

Rotate your Hue API credentials if:
- You suspect unauthorized access
- Following security best practices (periodic rotation)
- Credentials were accidentally exposed
- Sharing code or collaborating on the project

### Credential Rotation Steps

#### 1. Generate New API Key

Run the authentication script to generate a new API key:

```bash
# Method 1: Auto-discovery
python source/collectors/hue_auth.py

# Method 2: Manual IP (if auto-discovery fails)
python source/collectors/hue_auth.py --bridge-ip 192.168.1.XXX
```

**Important**: You must physically press the button on your Hue Bridge within 60 seconds when prompted.

#### 2. Verify New Credentials

The script will automatically update `config/secrets.yaml` with:
- New `api_key`
- `bridge_id` (for verification)

Check the file to confirm:

```bash
cat config/secrets.yaml
```

Expected format:
```yaml
hue:
  api_key: <new-key-here>
  bridge_id: <bridge-id>
```

#### 3. Test New Credentials

Verify the new credentials work:

```bash
# Quick verification
python source/verify_setup.py

# Or test data collection
make test-hue-sensors
```

#### 4. Revoke Old Credentials (Optional)

To revoke the old API key from the Hue Bridge:

1. Open the Hue app on your phone/tablet
2. Go to Settings → Hue Bridges → [Your Bridge]
3. Tap "Manage apps" or "Connected apps"
4. Find and remove any old/unused API keys

Alternatively, use the Hue API directly:

```bash
# List all API keys (whitelisted users)
curl -X GET http://<bridge-ip>/api/<current-api-key>/config

# Delete old API key
curl -X DELETE http://<bridge-ip>/api/<current-api-key>/config/whitelist/<old-api-key>
```

#### 5. Verify Git Protection

Ensure credentials never enter git:

```bash
# Check .gitignore contains secrets
grep "secrets.yaml" .gitignore

# Verify secrets.yaml is not tracked
git ls-files | grep secrets.yaml

# Should return nothing (or only .example files)
```

### Prevention Checklist

- [X] `config/secrets.yaml` in `.gitignore`
- [X] Only `.example` templates in git
- [X] Documentation references template files
- [X] CI/CD uses environment variables (when applicable)
- [ ] Regular credential rotation schedule (optional)

### Emergency Response

If credentials are accidentally committed:

1. **Immediately rotate credentials** (follow steps above)
2. **Remove from git history**:
   ```bash
   # Using git filter-repo (recommended)
   git filter-repo --path config/secrets.yaml --invert-paths
   
   # Or using BFG Repo-Cleaner
   bfg --delete-files secrets.yaml
   git reflog expire --expire=now --all
   git gc --prune=now --aggressive
   ```
3. **Force push** (⚠️ coordinate with team):
   ```bash
   git push --force --all
   ```
4. **Verify removal**:
   ```bash
   git log --all --full-history -- config/secrets.yaml
   ```

### Best Practices

1. **Never commit secrets**: Always use `.gitignore`
2. **Use templates**: Provide `.example` files for structure
3. **Environment variables**: For production/CI environments
4. **Periodic rotation**: Consider rotating quarterly
5. **Least privilege**: Create separate keys for different purposes
6. **Monitor access**: Review connected apps in Hue app regularly

### Additional Resources

- [Philips Hue API Documentation](https://developers.meethue.com/)
- [Hue Authentication Guide](./hue-authentication-guide.md)
- [Project Security Policies](./.github/agents/copilot-instructions.md)

---

**Last Updated**: 2025-11-19  
**Next Review**: 2026-02-19 (3 months)
