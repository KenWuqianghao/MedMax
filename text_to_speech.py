import azure.cognitiveservices.speech as speechsdk

def speech_synthesis_with_language(output_location, language, text):
    """performs speech synthesis to wav file specified spoken language"""
    # Creates an instance of a speech config with specified subscription key and service region.
    speech_config = speechsdk.SpeechConfig(subscription="13e23cf8341e44b8923af13e7088ab61", region="eastus")
    # Sets the synthesis language.
    speech_config.speech_synthesis_language = language
    # Creates a speech synthesizer for the specified language, using the default speaker as audio output.

    speech_synthesizer = speechsdk.SpeechSynthesizer(speech_config=speech_config, audio_config=None)

    ssml_pre = "<speak version='1.0' xmlns='http://www.w3.org/2001/10/synthesis' xmlns:mstts='https://www.w3.org/2001/mstts' xml:lang='en-US'> <voice name='en-US-JennyMultilingualNeural'> <lang xml:lang='"+ language +"'> " 
    ssml_post = "</lang> </voice> </speak>"
    ssml = ssml_pre + text + ssml_post

    # Receives a text from console input and synthesizes it to speaker.
    result = speech_synthesizer.speak_ssml_async(ssml).get()

    stream = speechsdk.AudioDataStream(result)
    file_name = output_location
    stream.save_to_wav_file(file_name)

    # Check result
    if result.reason == speechsdk.ResultReason.SynthesizingAudioCompleted:
        print("Speech synthesized for text [{}], and the audio was saved to [{}]".format(text, file_name))
    elif result.reason == speechsdk.ResultReason.Canceled:
        cancellation_details = result.cancellation_details
        print("Speech synthesis canceled: {}".format(cancellation_details.reason))
        if cancellation_details.reason == speechsdk.CancellationReason.Error:
            print("Error details: {}".format(cancellation_details.error_details))

# text = "我觉得今天的天气很美丽"
# speech_synthesis_with_language("zh-C", text)