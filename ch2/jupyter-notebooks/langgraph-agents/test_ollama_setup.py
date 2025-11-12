#!/usr/bin/env python3
"""
Quick test script to verify Ollama + Qwen2 setup for LangGraph agents.
Run this before starting the notebook tutorials.
"""

import sys
import subprocess

def check_ollama():
    """Check if Ollama is installed and running."""
    print("🔍 Checking Ollama installation...")
    try:
        result = subprocess.run(
            ['ollama', 'list'], 
            capture_output=True, 
            text=True, 
            timeout=5
        )
        if result.returncode == 0:
            print("✅ Ollama is installed and running\n")
            print("Available models:")
            print(result.stdout)
            return True, result.stdout
        else:
            print("❌ Ollama returned an error")
            return False, ""
    except FileNotFoundError:
        print("❌ Ollama not found. Install from: https://ollama.com")
        return False, ""
    except subprocess.TimeoutExpired:
        print("❌ Ollama command timed out. Is the service running?")
        return False, ""

def check_qwen2_model(model_list):
    """Check if Qwen2 model is available."""
    print("\n🔍 Checking for Qwen2 model...")
    if 'qwen2:0.5b' in model_list or 'qwen2' in model_list:
        print("✅ Qwen2 model is available!")
        return True
    else:
        print("❌ Qwen2:0.5b not found")
        print("📥 To install, run: ollama pull qwen2:0.5b")
        return False

def check_python_packages():
    """Check if required Python packages are installed."""
    print("\n🔍 Checking Python packages...")
    required = [
        'langgraph',
        'langchain_ollama',
        'langchain_community',
    ]
    
    missing = []
    for package in required:
        try:
            __import__(package)
            print(f"✅ {package}")
        except ImportError:
            print(f"❌ {package}")
            missing.append(package)
    
    if missing:
        print(f"\n📥 To install missing packages, run:")
        print(f"pip install {' '.join(missing)}")
        return False
    return True

def test_simple_query():
    """Test a simple query with Ollama."""
    print("\n🔍 Testing simple query with Qwen2...")
    try:
        from langchain_ollama import ChatOllama
        
        llm = ChatOllama(model="qwen2:0.5b", temperature=0)
        response = llm.invoke("Say 'Hello from Qwen2!' and nothing else.")
        
        print("✅ Successfully queried Qwen2!")
        print(f"Response: {response.content}")
        return True
    except Exception as e:
        print(f"❌ Error querying model: {e}")
        return False

def main():
    """Run all checks."""
    print("=" * 60)
    print("LangGraph + Ollama Setup Verification")
    print("=" * 60 + "\n")
    
    # Check Ollama
    ollama_ok, model_list = check_ollama()
    if not ollama_ok:
        sys.exit(1)
    
    # Check Qwen2 model
    model_ok = check_qwen2_model(model_list)
    
    # Check Python packages
    packages_ok = check_python_packages()
    
    # Test query if everything is installed
    if model_ok and packages_ok:
        test_ok = test_simple_query()
    else:
        print("\n⚠️  Skipping query test due to missing requirements")
        test_ok = False
    
    # Summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"Ollama:          {'✅' if ollama_ok else '❌'}")
    print(f"Qwen2 Model:     {'✅' if model_ok else '❌'}")
    print(f"Python Packages: {'✅' if packages_ok else '❌'}")
    print(f"Query Test:      {'✅' if test_ok else '❌'}")
    
    if all([ollama_ok, model_ok, packages_ok, test_ok]):
        print("\n🎉 All checks passed! You're ready to start the tutorials.")
        return 0
    else:
        print("\n⚠️  Some checks failed. Please address the issues above.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
