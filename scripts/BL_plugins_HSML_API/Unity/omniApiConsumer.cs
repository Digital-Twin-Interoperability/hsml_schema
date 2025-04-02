using System;
using System.Collections;
using UnityEngine;
using UnityEngine.Networking;
using Newtonsoft.Json.Linq;
using System.Collections.Concurrent;

public class omniApiConsumer : MonoBehaviour
{
    public string apiBaseUrl = "http://192.168.1.55:8000/consumer";
    public string topic = "cadre_a_qbnpru";
    public string privateKeyPath = @"C:\Users\Moonwalker\Desktop\Unity_scripts\HSMLdemo\demoRegisteredEntities\private_key_Viper_A.pem"; //Path to Producer Agent of Unity



    private UnityEngine.Vector3 targetPosition;
    private UnityEngine.Quaternion targetRotation;
    private bool isAuthorized = false;

    // Thread-safe queues to store positions and rotations
    private ConcurrentQueue<UnityEngine.Vector3> positionQueue = new ConcurrentQueue<UnityEngine.Vector3>();
    private ConcurrentQueue<UnityEngine.Quaternion> rotationQueue = new ConcurrentQueue<UnityEngine.Quaternion>();

    void Start()
    {
        StartCoroutine(AuthorizeAndStartConsumer());
    }

    void Update()
    {
        // Process queued positions and rotations in the main thread
        while (positionQueue.TryDequeue(out UnityEngine.Vector3 newPosition))
        {
            targetPosition = newPosition;
            Debug.Log($"Updated target position to: {targetPosition}");
        }

        while (rotationQueue.TryDequeue(out UnityEngine.Quaternion newRotation))
        {
            targetRotation = AdjustRotationAxis(newRotation);
            Debug.Log($"Updated target rotation to: {targetRotation.eulerAngles}");
        }

        // Smooth movement and rotation
        transform.position = UnityEngine.Vector3.Lerp(transform.position, targetPosition, Time.deltaTime * 5f);
        transform.rotation = UnityEngine.Quaternion.Slerp(transform.rotation, targetRotation, Time.deltaTime * 5f);
    }

    private IEnumerator AuthorizeAndStartConsumer()
    {
        byte[] privateKeyBytes = System.IO.File.ReadAllBytes(privateKeyPath);

        WWWForm authForm = new WWWForm();
        authForm.AddField("topic", topic);
        authForm.AddBinaryData("private_key", privateKeyBytes, "private_key.pem", "application/x-pem-file");
        string authUrlWithTopic = $"{apiBaseUrl}/authorize?topic={Uri.EscapeDataString(topic)}";

        using (UnityWebRequest authRequest = UnityWebRequest.Post(authUrlWithTopic, authForm)) //using (UnityWebRequest authRequest = UnityWebRequest.Post($"{apiBaseUrl}/authorize", authForm))
        {
            yield return authRequest.SendWebRequest();

            if (authRequest.result != UnityWebRequest.Result.Success)
            {
                Debug.LogError("Authorization failed: " + authRequest.error);
                yield break;
            }

            Debug.Log("Authorization successful.");
            isAuthorized = true;
        }

        using (UnityWebRequest startRequest = UnityWebRequest.Post($"{apiBaseUrl}/start?topic={topic}", ""))
        {
            yield return startRequest.SendWebRequest();

            if (startRequest.result != UnityWebRequest.Result.Success)
            {
                Debug.LogError("Failed to start consumer: " + startRequest.error);
                yield break;
            }

            Debug.Log("Consumer started.");
        }

        StartCoroutine(PollLatestMessages());
    }

    private IEnumerator PollLatestMessages()
    {
        while (isAuthorized)
        {
            using (UnityWebRequest messageRequest = UnityWebRequest.Get($"{apiBaseUrl}/latest-message?topic={topic}"))
            {
                yield return messageRequest.SendWebRequest();

                if (messageRequest.result == UnityWebRequest.Result.Success)
                {
                    try
                    {
                        var messageJson = JObject.Parse(messageRequest.downloadHandler.text);
                        var newPosition = ExtractPosition(messageJson);
                        var newRotation = AdjustRotationAxis(ExtractRotation(messageJson));

                        positionQueue.Enqueue(newPosition);
                        rotationQueue.Enqueue(newRotation);
                    }
                    catch (Exception ex)
                    {
                        Debug.LogError("Error parsing message: " + ex.Message);
                    }
                }

                yield return new WaitForSeconds(0.1f); // 100ms polling interval
            }
        }
    }

    private UnityEngine.Vector3 ExtractPosition(JObject message)
    {
        try
        {
            var positionArray = message["position"] as JArray;
            if (positionArray != null)
            {
                float x = positionArray[0]?["value"]?.ToObject<float>() ?? 0f;
                float y = positionArray[1]?["value"]?.ToObject<float>() ?? 0f;
                float z = positionArray[2]?["value"]?.ToObject<float>() ?? 0f;

                // Adjust for Unity's coordinate system
                return new UnityEngine.Vector3(x, z, y);
            }
        }
        catch (Exception e)
        {
            Debug.LogError($"Error extracting position: {e.Message}");
        }
        return UnityEngine.Vector3.zero;
    }

    private UnityEngine.Quaternion ExtractRotation(JObject message)
    {
        try
        {
            var rotationArray = message["rotation"] as JArray;
            if (rotationArray != null)
            {
                float rx = rotationArray[0]?["value"]?.ToObject<float>() ?? 0f;
                float ry = rotationArray[1]?["value"]?.ToObject<float>() ?? 0f;
                float rz = rotationArray[2]?["value"]?.ToObject<float>() ?? 0f;
                float w = rotationArray[3]?["value"]?.ToObject<float>() ?? 1f; // w value is now part of the rotation

                return new UnityEngine.Quaternion(rx, ry, rz, w);
            }
        }
        catch (Exception e)
        {
            Debug.LogError($"Error extracting rotation: {e.Message}");
        }
        return UnityEngine.Quaternion.identity;
    }

    private UnityEngine.Quaternion AdjustRotationAxis(UnityEngine.Quaternion rotation)
    {
        var originalRotQuat = new System.Numerics.Quaternion(rotation.x, rotation.y, rotation.z, rotation.w);

        var rotationXQuat = System.Numerics.Quaternion.CreateFromAxisAngle(new System.Numerics.Vector3(1, 0, 0), (float)-Math.PI / 2);
        var rotationYQuat = System.Numerics.Quaternion.CreateFromAxisAngle(new System.Numerics.Vector3(0, 1, 0), (float)Math.PI);

        var worldRotation = System.Numerics.Quaternion.Multiply(rotationYQuat, rotationXQuat);
        worldRotation = System.Numerics.Quaternion.Multiply(originalRotQuat, worldRotation);
        worldRotation = System.Numerics.Quaternion.Multiply(rotationXQuat, worldRotation);

        return new UnityEngine.Quaternion(-worldRotation.X, -worldRotation.Y, worldRotation.Z, worldRotation.W);
    }
}
