# Demo: 16×10 RGB LED Matrix with Raspberry Pi Pico

Year-end demo featuring a 16×10 RGB LED matrix powered by Raspberry Pi Pico. The code is written entirely in MicroPython.



**Ingredients**

* Raspberry Pi Pico WH (RP2040 microcontroller)
* Pico Dual Expander (Waveshare)
* 16×10 RGB LED matrix (Waveshare)
* Based on Waveshare demo code (see [here](https://www.waveshare.com/wiki/Pico-RGB-LED))
* Translucent paper to diffuse and soften the light



**Implementation**

This project implements a festive animation sequence for a 16×10 LED grid using an object-oriented framework. A base `Animation` class provides lifecycle management (start, stop, reset), while an `AnimationManager` orchestrates multiple animations with frame-precise timing. The implementation uses integer-indexed dictionaries for pixel storage and supports multiple bitmap fonts (6×6 through 9×9) with variable-width rendering. Scenes are authored in portrait mode and transformed to the hardware's landscape orientation. Frame-based scheduling enables seamless multi-scene compositions with layered effects.



**Result**

![The resulting GIF](./result.gif)



