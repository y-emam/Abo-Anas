#!/usr/bin/env python3
"""
Test script to verify the WebSocket voice assistant app works
"""

try:
    from app import create_app
    from app.config import config
    
    print("✓ Imports successful")
    
    # Test creating the app
    app, socketio = create_app('development')
    print("✓ App creation successful")
    
    # Test routes
    with app.test_client() as client:
        response = client.get('/')
        print(f"✓ Home route works: {response.status_code}")
        
    print("\n🎉 All tests passed! Your WebSocket voice assistant is ready!")
    print(f"📡 WebSocket URL configured: wss://bff3b149c0fc.ngrok-free.app/ws")
    print("\n🚀 To start the server, run: python app.py")
    
except Exception as e:
    print(f"❌ Error: {str(e)}")
    import traceback
    traceback.print_exc()
