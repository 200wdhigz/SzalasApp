"""
Test PWA functionality
"""
import os
import json

def test_pwa_files_exist():
    """Test that all PWA files exist."""
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    files_to_check = [
        'static/manifest.json',
        'static/service-worker.js',
        'static/assets/js/pwa-install.js',
        'static/icons/icon-192x192.png',
        'static/icons/icon-512x512.png',
    ]

    for file_path in files_to_check:
        full_path = os.path.join(base_dir, file_path)
        assert os.path.exists(full_path), f"Missing PWA file: {file_path}"
        print(f"✓ Found: {file_path}")

def test_manifest_valid():
    """Test that manifest.json is valid JSON with required fields."""
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    manifest_path = os.path.join(base_dir, 'static', 'manifest.json')

    with open(manifest_path, 'r', encoding='utf-8') as f:
        manifest = json.load(f)

    required_fields = ['name', 'short_name', 'start_url', 'display', 'icons']
    for field in required_fields:
        assert field in manifest, f"Missing required field in manifest: {field}"
        print(f"✓ Manifest has '{field}': {manifest[field] if field != 'icons' else f'{len(manifest[field])} icons'}")

    # Check icons
    assert len(manifest['icons']) >= 2, "Manifest should have at least 2 icons"
    for icon in manifest['icons']:
        assert 'src' in icon and 'sizes' in icon and 'type' in icon
        print(f"✓ Icon: {icon['sizes']} - {icon['src']}")

def test_service_worker_content():
    """Test that service worker has required event listeners."""
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    sw_path = os.path.join(base_dir, 'static', 'service-worker.js')

    with open(sw_path, 'r', encoding='utf-8') as f:
        content = f.read()

    required_events = ['install', 'activate', 'fetch']
    for event in required_events:
        assert f"addEventListener('{event}'" in content, f"Service worker missing '{event}' event"
        print(f"✓ Service worker has '{event}' event listener")

def test_pwa_install_script():
    """Test that PWA install script exists and has required functionality."""
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    script_path = os.path.join(base_dir, 'static', 'assets', 'js', 'pwa-install.js')

    with open(script_path, 'r', encoding='utf-8') as f:
        content = f.read()

    required_features = [
        'beforeinstallprompt',
        'serviceWorker',
        'register',
        'pwa-install-button'
    ]

    for feature in required_features:
        assert feature in content, f"PWA install script missing: {feature}"
        print(f"✓ PWA install script has: {feature}")

if __name__ == '__main__':
    print("=" * 60)
    print("PWA Installation Test")
    print("=" * 60)

    try:
        print("\n1. Checking PWA files...")
        test_pwa_files_exist()

        print("\n2. Validating manifest.json...")
        test_manifest_valid()

        print("\n3. Checking service worker...")
        test_service_worker_content()

        print("\n4. Checking PWA install script...")
        test_pwa_install_script()

        print("\n" + "=" * 60)
        print("✅ All PWA tests passed!")
        print("=" * 60)
        print("\nYour app is ready to be installed as a PWA!")
        print("Next steps:")
        print("1. Ensure your app is served over HTTPS in production")
        print("2. Test installation on Chrome/Edge (desktop or mobile)")
        print("3. Check DevTools → Application → Manifest & Service Workers")
        print("4. Run Lighthouse PWA audit for additional insights")

    except AssertionError as e:
        print(f"\n❌ Test failed: {e}")
        exit(1)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        exit(1)

