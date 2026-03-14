using UnityEngine;
using UnityEngine.Networking;
using UnityEngine.InputSystem;
using System.Collections;

public class NPCClient : MonoBehaviour
{
    public string serverUrl  = "http://localhost:8000/npc";
    public string voiceUrl   = "http://localhost:8000/voice";
    public string npcId      = "villager_01";
    public int    maxSeconds = 10;

    private bool      _isBusy      = false;
    private bool      _isRecording = false;
    private AudioClip _clip;

    void Update()
    {
        if (_isBusy) return;

        // Push-to-Talk — hold Space to record, release to send
        if (Keyboard.current.spaceKey.wasPressedThisFrame)
            StartRecording();

        if (Keyboard.current.spaceKey.wasReleasedThisFrame)
            StartCoroutine(StopAndSend());
    }

    // ── Text request ─────────────────────────────────────────
    public void AskNPC(string text)
    {
        StartCoroutine(Send(text));
    }

    IEnumerator Send(string text)
    {
        _isBusy = true;

        string encodedText = UnityWebRequest.EscapeURL(text);
        string fullUrl = serverUrl + "?text=" + encodedText;

        using UnityWebRequest www = UnityWebRequest.Get(fullUrl);
        yield return www.SendWebRequest();

        if (www.result == UnityWebRequest.Result.Success)
            Debug.Log("NPC: " + www.downloadHandler.text);
        else
            Debug.LogError("Request error: " + www.error);

        _isBusy = false;
    }

    // ── Voice request ────────────────────────────────────────
    void StartRecording()
    {
        if (_isRecording) return;
        _isRecording = true;
        _clip = Microphone.Start(null, false, maxSeconds, 16000);
        // 16000 Hz — standard for STT. For device compatibility check:
        // Microphone.GetDeviceCaps(null, out int minFreq, out int maxFreq)
        Debug.Log("[Voice] Recording... (hold Space)");
    }

    IEnumerator StopAndSend()
    {
        if (!_isRecording) yield break;

        int recordedSamples = Microphone.GetPosition(null);
        Microphone.End(null);
        _isRecording = false;

        // Wait one frame — Microphone needs time to flush last samples
        yield return null;

        AudioClip trimmed = TrimClip(_clip, recordedSamples);

        if (trimmed == null || recordedSamples < 1600) // < 0.1 sec — ignore
        {
            Debug.LogWarning("[Voice] Recording too short, ignoring.");
            yield break;
        }

        Debug.Log($"[Voice] Recorded {recordedSamples / 16000f:F1} sec. Sending...");

        _isBusy = true;

        byte[] wav = WavUtility.FromAudioClip(trimmed);
        string worldJson = GetComponent<WorldContextBuilder>().GetContextJson();

        WWWForm form = new WWWForm();
        form.AddBinaryData("file",         wav,       "voice.wav", "audio/wav");
        form.AddField("world_context",     worldJson);
        form.AddField("npc_id",            npcId);

        using UnityWebRequest www = UnityWebRequest.Post(voiceUrl, form);
        www.downloadHandler = new DownloadHandlerAudioClip(voiceUrl, AudioType.MPEG);

        yield return www.SendWebRequest();

        if (www.result == UnityWebRequest.Result.Success)
        {
            string decisionJson = www.GetResponseHeader("X-NPC-Decision");
            AudioClip clip = DownloadHandlerAudioClip.GetContent(www);

            if (!string.IsNullOrEmpty(decisionJson))
            {
                GetComponent<NPCController>().ApplyDecision(decisionJson, clip);
            }
            else
            {
                // Header empty — just play audio
                GetComponent<AudioSource>().PlayOneShot(clip);
            }

            Debug.Log("[Voice] NPC says: " + decisionJson);
        }
        else
        {
            Debug.LogError("[Voice] Error: " + www.error);
        }

        _isBusy = false;
    }

    AudioClip TrimClip(AudioClip source, int samples)
    {
        if (source == null || samples <= 0) return null;

        float[] data = new float[samples * source.channels];
        source.GetData(data, 0);

        AudioClip trimmed = AudioClip.Create(
            "voice_trimmed", samples, source.channels, source.frequency, false
        );
        trimmed.SetData(data, 0);
        return trimmed;
    }
}
