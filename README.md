# GateLock

GateLock is an access-control platform with integrated Face Recognition technology.

Its purpose is to serve as a security system capable of detecting, recognizing, and allowing access to a given room.

---

## Face Recognition Proof of Concept

A working facial-recognition prototype is available here:

**[Face Recognition POC](Spikes/FaceRecognitionPOC)**

This POC demonstrates:
- Real-time face detection and recognition running on a Raspberry Pi 5  
- InsightFace models handling detection, embedding generation, and recognition  
- Database generation from user-provided photos  
- Live camera-based identification  
- Video-based recognition with parameterized performance options (frame skipping, resizing, and optional video output)

It is meant as a reference and testing ground before integrating biometric authentication into the main GateLock system.

---

## Status

GateLock is currently under active development.  
Modules inside `/spikes` are experimental and may change or be refactored before being included in the main core.

---

## License

To be defined.
