import azure.cognitiveservices.speech as speechsdk
import streamlit as st
from audiorecorder import audiorecorder
from pydub import AudioSegment
import os

def speech_from_mic(input_code, audio):
    if os.path.exists("input.wav"):
        existing_audio = AudioSegment.from_file("input.wav")
        if len(audio) > 0 and audio == existing_audio:
            return None
        else:
            audio.export("input.wav", format="wav")
            return speech_from_file(input_code)
    else:
        if len(audio) > 0:
            audio.export("input.wav", format="wav")
            return speech_from_file(input_code)
        else:
            return None
        
def speech_from_file(lang_code):
    # str: language code (ex. "en-US")
    # This example requires environment variables named "SPEECH_KEY" and "SPEECH_REGION"
    speech_config = speechsdk.SpeechConfig(subscription="13e23cf8341e44b8923af13e7088ab61",
                                           region="eastus")
    speech_config.speech_recognition_language=lang_code 

    audio_config = speechsdk.audio.AudioConfig(filename="./input.wav")
    speech_recognizer = speechsdk.SpeechRecognizer(speech_config=speech_config, audio_config=audio_config)

    print("Detecting from input file now.")
    speech_recognition_result = speech_recognizer.recognize_once_async().get()

    if speech_recognition_result.reason == speechsdk.ResultReason.RecognizedSpeech:
        print("Recognized: {}".format(speech_recognition_result.text))
    elif speech_recognition_result.reason == speechsdk.ResultReason.NoMatch:
        print("No speech could be recognized: {}".format(speech_recognition_result.no_match_details))
    elif speech_recognition_result.reason == speechsdk.ResultReason.Canceled:
        cancellation_details = speech_recognition_result.cancellation_details
        print("Speech Recognition canceled: {}".format(cancellation_details.reason))
        if cancellation_details.reason == speechsdk.CancellationReason.Error:
            print("Error details: {}".format(cancellation_details.error_details))
            print("Did you set the speech resource key and region values?")
    return speech_recognition_result.text
