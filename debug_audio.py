
import sounddevice as sd
import numpy as np
import time

def debug_audio():
    print("--- Audio Device Debug ---")
    try:
        print(sd.query_devices())
    except Exception as e:
        print(f"Error querying devices: {e}")
        return

    print("\n--- Recording Test (5 seconds) ---")
    duration = 5.0
    sample_rate = 16000
    
    try:
        # Record
        print("Recording...")
        audio = sd.rec(int(duration * sample_rate), samplerate=sample_rate, channels=1, dtype='float32')
        
        # Print RMS levels while recording (simulated by checking chunks if we did streams, 
        # but here we just wait and check the result for simplicity)
        for i in range(5):
            time.sleep(1)
            print(f"Recording... {i+1}/5")
        
        sd.wait()
        print("Recording complete.")
        
        # Analyze
        audio_flat = audio.flatten()
        max_amp = np.max(np.abs(audio_flat))
        mean_amp = np.mean(np.abs(audio_flat))
        rms = np.sqrt(np.mean(audio_flat**2))
        
        print(f"\n--- Analysis ---")
        print(f"Max Amplitude: {max_amp:.6f}")
        print(f"Mean Amplitude: {mean_amp:.6f}")
        print(f"RMS Power:     {rms:.6f}")
        
        if rms < 0.001:
            print("\n[WARNING] Audio is extremely quiet. Check microphone mute or gain.")
        else:
            print("\n[SUCCESS] Audio detected!")
            
    except Exception as e:
        print(f"\n[ERROR] Recording failed: {e}")

if __name__ == "__main__":
    debug_audio()
