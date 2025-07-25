#!/usr/bin/env python3
"""Test script for DXT build with version updates."""

import json
import shutil
import subprocess
import sys
from pathlib import Path


def test_dxt_build(test_version="2.2.0"):
    """Test the DXT build process with version updates."""
    print(f"Testing DXT build with version: {test_version}")
    print("-" * 50)
    
    # Backup original manifest.json
    print("1. Backing up manifest.json...")
    shutil.copy("manifest.json", "manifest.json.test-backup")
    
    try:
        # Read current manifest
        with open("manifest.json", "r") as f:
            manifest = json.load(f)
        
        # Show current versions
        current_version = manifest.get("version", "unknown")
        current_scm_version = manifest.get("server", {}).get("mcp_config", {}).get("env", {}).get("SETUPTOOLS_SCM_PRETEND_VERSION", "unknown")
        print(f"\nCurrent versions:")
        print(f"  - manifest version: {current_version}")
        print(f"  - SETUPTOOLS_SCM_PRETEND_VERSION: {current_scm_version}")
        
        # Update versions
        print(f"\n2. Updating manifest.json to version {test_version}...")
        manifest["version"] = test_version
        if "server" in manifest and "mcp_config" in manifest["server"] and "env" in manifest["server"]["mcp_config"]:
            manifest["server"]["mcp_config"]["env"]["SETUPTOOLS_SCM_PRETEND_VERSION"] = test_version
        
        # Write updated manifest
        with open("manifest.json", "w") as f:
            json.dump(manifest, f, indent=2)
            f.write("\n")
        
        # Verify updates
        print("\n3. Verifying updates...")
        result = subprocess.run(
            ["jq", ".version, .server.mcp_config.env.SETUPTOOLS_SCM_PRETEND_VERSION", "manifest.json"],
            capture_output=True,
            text=True
        )
        print("Updated versions:")
        print(result.stdout)
        
        # Create dxt directory
        print("4. Creating dxt directory...")
        Path("dxt").mkdir(exist_ok=True)
        
        # Build DXT with environment variable
        print(f"\n5. Building DXT with SETUPTOOLS_SCM_PRETEND_VERSION={test_version}...")
        env = dict(os.environ)
        env["SETUPTOOLS_SCM_PRETEND_VERSION"] = test_version
        
        result = subprocess.run(
            ["make", "dxt"],
            env=env,
            capture_output=True,
            text=True
        )
        
        print("\nBuild output:")
        print(result.stdout)
        if result.stderr:
            print("Build errors:")
            print(result.stderr)
        
        if result.returncode != 0:
            print(f"\n❌ Build failed with return code: {result.returncode}")
            return False
        
        # Check created files
        print("\n6. Checking created DXT files...")
        dxt_files = list(Path("dxt").glob("*.dxt*"))
        if dxt_files:
            print("✅ DXT files created:")
            for file in dxt_files:
                size = file.stat().st_size
                print(f"  - {file.name} ({size:,} bytes)")
        else:
            print("❌ No DXT files found!")
            return False
        
        print("\n✅ Test completed successfully!")
        return True
        
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        return False
        
    finally:
        # Always restore original manifest.json
        print("\n7. Restoring original manifest.json...")
        if Path("manifest.json.test-backup").exists():
            shutil.move("manifest.json.test-backup", "manifest.json")
            print("✅ Original manifest.json restored")


if __name__ == "__main__":
    import os
    
    # Get test version from command line or use default
    test_version = sys.argv[1] if len(sys.argv) > 1 else "2.2.0"
    
    # Run the test
    success = test_dxt_build(test_version)
    sys.exit(0 if success else 1)