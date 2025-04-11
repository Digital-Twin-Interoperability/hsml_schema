using System;
using System.Text;
using System.Collections;
using System.Security.Cryptography;
using UnityEngine;
using Newtonsoft.Json.Linq;
using System.Numerics;
using UnityEngine.Networking;
using System.IO;

public class switchOmniApiConsumer : MonoBehaviour
{
    // API endpoint settings – update these as necessary.
    public string apiBaseUrl = "http://192.168.1.55:8000/producer";
    public string topic = "feedback_channel";
    public string privateKeyPath = @"C:\Users\Moonwalker\Desktop\Unity_scripts\HSMLdemo\demoRegisteredEntities\private_key_Feedback_Channel.pem";

    // Optionally, if your API uses a separate endpoint for sending messages
    // you can either append the route when sending or define a separate variable.
    // In this example, we append the route to the apiBaseUrl.
    // private string hsmlApiUrl = "http://192.168.1.55:8000/producer/send-message";
    
    private UnityEngine.Vector3 lastPosition;
    private UnityEngine.Quaternion lastRotation;
    private bool isAuthenticated = false;

    void Start()
    {
        lastPosition = transform.position;
        lastRotation = transform.rotation;
        // Start authentication before sending messages.
        StartCoroutine(AuthenticateWithAPI());
        Debug.Log("Switch HSML API Producer initialized.");
    }

    void Update()
    {
        // Only attempt to send a message if authentication is complete and the transform has changed.
        if (isAuthenticated && HasTransformChanged())
        {
            JObject hsmlMessage = BuildHSMLMessage();
            StartCoroutine(SendMessageToAPI(hsmlMessage));
            lastPosition = transform.position;
            lastRotation = transform.rotation;
        }
    }

    /// <summary>
    /// Check if the position or rotation has changed since the last message.
    /// </summary>
    private bool HasTransformChanged()
    {
        return transform.position != lastPosition || transform.rotation != lastRotation;
    }

    /// <summary>
    /// Generate a unique identifier for this message using MD5 hash.
    /// </summary>
    private string GenerateUniqueSchemaId()
    {
        string inputData = $"{gameObject.name}_{transform.position}_{DateTime.Now.Ticks}";
        using (MD5 md5 = MD5.Create())
        {
            byte[] hashBytes = md5.ComputeHash(Encoding.UTF8.GetBytes(inputData));
            StringBuilder sb = new StringBuilder();
            foreach (byte b in hashBytes)
                sb.Append(b.ToString("X2"));
            return sb.ToString();
        }
    }

    /// <summary>
    /// Construct the HSML message as a JSON object.
    /// This includes additional fields for rotation wheels and other properties.
    /// </summary>
    private JObject BuildHSMLMessage()
    {
        string schemaId = GenerateUniqueSchemaId();
        UnityEngine.Quaternion adjustedRotation = AdjustRotationAxis(transform.rotation);

        JObject message = new JObject
        {
            { "@context", "https://digital-twin-interoperability.github.io/hsml-schema-context/hsml.jsonld" },
            { "@type", "Agent" },
            { "name", gameObject.name },
            { "swid", "did:key:generateBeforeDemoWithRegistration" },
            { "url", "1GBcmwJh2rQ4CSR3_CiDyF6oVdOxz6hLG" },
            { "creator", new JObject {
                { "@type", "Person" },
                { "name", "Jared Carrillo" },
                { "swid", "did:key:personMustBeRegisteredBefore" }
            }},
            { "dateCreated", DateTime.UtcNow.ToString("yyyy-MM-dd") },
            { "dateModified", DateTime.UtcNow.ToString("yyyy-MM-dd") },
            { "encodingFormat", "application/x-obj" },
            { "contentUrl", "https://example.com/models/3dmodel-001.obj" },
            { "description", "Continuous game object data with full schema" },
            { "platform", "Unity" },
            { "inControl", true },
            { "schemaId", schemaId },
            { "spaceLocation", new JArray {
                new JObject { { "@type", "Hyperspace" }, { "name", "Moon" } }
            }},
            { "position", new JArray {
                new JObject { { "@type", "schema:PropertyValue" }, { "name", "xCoordinate" }, { "value", transform.position.x } },
                new JObject { { "@type", "schema:PropertyValue" }, { "name", "yCoordinate" }, { "value", transform.position.y } },
                new JObject { { "@type", "schema:PropertyValue" }, { "name", "zCoordinate" }, { "value", transform.position.z } }
            }},
            { "rotation", new JArray {
                new JObject { { "@type", "schema:PropertyValue" }, { "name", "rx" }, { "value", adjustedRotation.x } },
                new JObject { { "@type", "schema:PropertyValue" }, { "name", "ry" }, { "value", adjustedRotation.y } },
                new JObject { { "@type", "schema:PropertyValue" }, { "name", "rz" }, { "value", adjustedRotation.z } },
                new JObject { { "@type", "schema:PropertyValue" }, { "name", "w" }, { "value", adjustedRotation.w } }
            }},
            { "rotationWheels", new JArray {
                new JObject { { "@type", "schema:PropertyValue" }, { "name", "LF" }, { "value", 45.0 } },
                new JObject { { "@type", "schema:PropertyValue" }, { "name", "LR" }, { "value", 45.0 } },
                new JObject { { "@type", "schema:PropertyValue" }, { "name", "RF" }, { "value", 45.0 } },
                new JObject { { "@type", "schema:PropertyValue" }, { "name", "RR" }, { "value", 45.0 } }
            }},
            { "additionalProperty", new JArray {
                new JObject { { "@type", "schema:PropertyValue" }, { "name", "scale" }, { "value", 100 } }
            }}
        };

        return message;
    }

    /// <summary>
    /// Adjusts the rotation values to align with Unity’s coordinate system.
    /// The method replicates the rotation adjustments made in your Kafka scripts.
    /// </summary>
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

    /// <summary>
    /// Coroutine to authenticate with the HSML API using a private key.
    /// </summary>
    private IEnumerator AuthenticateWithAPI()
    {
        byte[] privateKeyData = File.ReadAllBytes(privateKeyPath);
        WWWForm form = new WWWForm();
        form.AddBinaryData("private_key", privateKeyData, "private_key.pem", "application/x-pem-file");

        string authUrl = $"{apiBaseUrl}/authenticate?topic={Uri.EscapeDataString(topic)}";

        using (UnityWebRequest www = UnityWebRequest.Post(authUrl, form))
        {
            yield return www.SendWebRequest();

            if (www.result != UnityWebRequest.Result.Success)
            {
                Debug.LogError($"Authentication failed: {www.error}");
                isAuthenticated = false;
            }
            else
            {
                Debug.Log("Authentication successful.");
                isAuthenticated = true;
            }
        }
    }

    /// <summary>
    /// Coroutine to send the HSML message to the API endpoint via an HTTP POST request.
    /// </summary>
    private IEnumerator SendMessageToAPI(JObject hsmlMessage)
    {
        string jsonBody = hsmlMessage.ToString();
        byte[] bodyRaw = Encoding.UTF8.GetBytes(jsonBody);

        // Send the message via the API’s send-message endpoint.
        string sendUrl = $"{apiBaseUrl}/send-message?topic={Uri.EscapeDataString(topic)}";
        UnityWebRequest www = new UnityWebRequest(sendUrl, "POST");
        www.uploadHandler = new UploadHandlerRaw(bodyRaw);
        www.downloadHandler = new DownloadHandlerBuffer();
        www.SetRequestHeader("Content-Type", "application/json");

        yield return www.SendWebRequest();

        if (www.result != UnityWebRequest.Result.Success)
        {
            Debug.LogError($"Message send failed: {www.error} | {www.downloadHandler.text}");
        }
        else
        {
            Debug.Log("Message sent successfully.");
        }
    }
}
