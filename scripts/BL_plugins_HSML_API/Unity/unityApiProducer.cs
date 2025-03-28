using System;
using System.Text;
using System.Collections;
using System.Security.Cryptography;
using UnityEngine;
using Newtonsoft.Json.Linq;
using System.Numerics;
using UnityEngine.Networking;
using System.IO;

public class UnityHsmlProducer : MonoBehaviour
{
    private string hsmlApiUrl = "http://192.168.1.55:8000/producer/send-message";  // Update with your API
    private string topic = "viperA_new_topic";
    private string privateKeyPath = "C:/Path/To/private_key_viperA.pem";
    private UnityEngine.Vector3 lastPosition;
    private UnityEngine.Quaternion lastRotation;
    private bool isAuthenticated = false;

    void Start()
    {   
        lastPosition = transform.position;
        lastRotation = transform.rotation;
        StartCoroutine(AuthenticateWithAPI());
        Debug.Log("HSML Producer initialized.");
    }

    void Update()
    {
        if (isAuthenticated && HasTransformChanged())
        {
            JObject hsmlMessage = BuildHSMLMessage();
            StartCoroutine(SendMessageToAPI(hsmlMessage));
            lastPosition = transform.position;
            lastRotation = transform.rotation;
        }
    }

    private bool HasTransformChanged()
    {
        return transform.position != lastPosition || transform.rotation != lastRotation;
    }

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

    private JObject BuildHSMLMessage()
    {
        string schemaId = GenerateUniqueSchemaId(); // Optional unique ID per message
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
            { "dateModified", DateTime.UtcNow.ToString("yyyy-MM-ddTHH:mm:ss") },
            { "encodingFormat", "application/x-obj" },
            { "contentUrl", "https://example.com/models/3dmodel-001.obj" },
            { "description", "Unity simulation agent HSML" },
            { "platform", "Unity" },
            { "inControl", true },
            { "spaceLocation", new JArray { new JObject { { "@type", "Hyperspace" }, { "name", "Moon" } } } },
            { "position", new JArray {
                new JObject { { "@type", "schema:PropertyValue" }, { "name", "xCoordinate" }, { "value", transform.position.x } },
                new JObject { { "@type", "schema:PropertyValue" }, { "name", "yCoordinate" }, { "value", transform.position.y } },
                new JObject { { "@type", "schema:PropertyValue" }, { "name", "zCoordinate" }, { "value", transform.position.z } }
            }},
            { "rotation", new JArray {
                new JObject { { "@type", "schema:PropertyValue" }, { "name", "rx" }, { "value", adjustedRotation.x } },
                new JObject { { "@type", "schema:PropertyValue" }, { "name", "ry" }, { "value", adjustedRotation.y } },
                new JObject { { "@type", "schema:PropertyValue" }, { "name", "rz" }, { "value", adjustedRotation.z } },
                new JObject { { "@type", "schema:PropertyValue" }, { "name", "w" },  { "value", adjustedRotation.w } }
            }},
            { "additionalProperty", new JArray {
                new JObject { { "@type", "schema:PropertyValue" }, { "name", "scale" }, { "value", 100 } }
            }}
        };

        return message;
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

    private IEnumerator AuthenticateWithAPI()
    {
        byte[] privateKeyData = System.IO.File.ReadAllBytes(privateKeyPath);

        WWWForm form = new WWWForm();
        form.AddField("topic", topic);
        form.AddBinaryData("private_key", privateKeyData, "private_key.pem", "application/x-pem-file");

        using (UnityWebRequest www = UnityWebRequest.Post($"{apiBaseUrl}/authenticate", form))
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

    private IEnumerator SendMessageToAPI(JObject hsmlMessage)
    {
        byte[] messageBytes = Encoding.UTF8.GetBytes(hsmlMessage.ToString());
        WWWForm form = new WWWForm();
        form.AddField("topic", topic);
        form.AddBinaryData("message", messageBytes, "message.json", "application/json");

        using (UnityWebRequest www = UnityWebRequest.Post($"{apiBaseUrl}/send-message", form))
        {
            yield return www.SendWebRequest();

            if (www.result != UnityWebRequest.Result.Success)
            {
                Debug.LogError($"Message send failed: {www.error}");
            }
            else
            {
                Debug.Log("Message sent successfully.");
            }
        }
    }
}
