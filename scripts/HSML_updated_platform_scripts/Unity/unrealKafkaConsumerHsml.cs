using System;
using System.Collections.Concurrent;
using System.Threading;
using UnityEngine;
using Confluent.Kafka;
using Newtonsoft.Json.Linq;
using System.Numerics;

public class unrealKafkaConsumer : MonoBehaviour
{
    private IConsumer<string, string> consumer;
    private string kafkaTopic = "unreal-hsml-topic";
    private UnityEngine.Vector3 targetPosition; // UnityEngine.Vector3 for position
    private UnityEngine.Quaternion targetRotation; // UnityEngine.Quaternion for rotation
    private Thread consumerThread;
    private bool isRunning = true;

    // Thread-safe queues to store positions and rotations
    private ConcurrentQueue<UnityEngine.Vector3> positionQueue = new ConcurrentQueue<UnityEngine.Vector3>();
    private ConcurrentQueue<UnityEngine.Quaternion> rotationQueue = new ConcurrentQueue<UnityEngine.Quaternion>();

    void Start()
    {
        // Kafka consumer configuration
        var config = new ConsumerConfig
        {
            BootstrapServers = "192.168.1.55:9092", // Replace with your Kafka server IP
            GroupId = "unreal-consumer-group",
            AutoOffsetReset = AutoOffsetReset.Earliest,
            EnableAutoCommit = true
        };

        consumer = new ConsumerBuilder<string, string>(config).Build();
        consumer.Subscribe(kafkaTopic);

        // Initialize the consumer thread
        consumerThread = new Thread(ReadKafkaMessages);
        consumerThread.Start();
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

        // Smoothly move the GameObject to the target position
        transform.position = UnityEngine.Vector3.Lerp(transform.position, targetPosition, Time.deltaTime * 5f);

        // Apply the rotation to the GameObject
        transform.rotation = UnityEngine.Quaternion.Slerp(transform.rotation, targetRotation, Time.deltaTime * 5f);
    }

    private void ReadKafkaMessages()
    {
        while (isRunning)
        {
            try
            {
                var consumeResult = consumer.Consume(TimeSpan.FromMilliseconds(100));
                if (consumeResult != null && !string.IsNullOrEmpty(consumeResult.Value))
                {
                    Debug.Log($"Received Kafka message: {consumeResult.Value}");
                    var message = JObject.Parse(consumeResult.Value);

                    // Extract position
                    UnityEngine.Vector3 position = ExtractPosition(message);
                    positionQueue.Enqueue(position);

                    // Extract rotation
                    UnityEngine.Quaternion rotation = ExtractRotation(message);
                    rotationQueue.Enqueue(rotation);
                }
            }
            catch (ConsumeException e)
            {
                Debug.LogError($"Error consuming Kafka message: {e.Error.Reason}");
            }
            catch (Exception e)
            {
                Debug.LogError($"Unexpected error: {e.Message}");
            }
        }
    }

    private UnityEngine.Vector3 ExtractPosition(JObject message)
    {
        try
        {
            var positionArray = message["position"] as JArray;
            float x = positionArray?[0]["value"]?.ToObject<float>() ?? 0f;
            float y = positionArray?[1]["value"]?.ToObject<float>() ?? 0f;
            float z = positionArray?[2]["value"]?.ToObject<float>() ?? 0f;

            return new UnityEngine.Vector3(x, z, y); // Adjusted for Unreal's coordinate system
        }
        catch (Exception e)
        {
            Debug.LogError($"Error extracting position: {e.Message}");
            return UnityEngine.Vector3.zero;
        }
    }

    private UnityEngine.Quaternion ExtractRotation(JObject message)
    {
        try
        {
            var rotationArray = message["rotation"] as JArray;
            float rx = rotationArray?[0]["value"]?.ToObject<float>() ?? 0f;
            float ry = rotationArray?[1]["value"]?.ToObject<float>() ?? 0f;
            float rz = rotationArray?[2]["value"]?.ToObject<float>() ?? 0f;
            float w = rotationArray?[3]["value"]?.ToObject<float>() ?? 1f;

            var additionalProperties = message["additionalProperty"] as JArray;
            float scale = additionalProperties?[0]["value"]?.ToObject<float>() ?? 100f;

            return new UnityEngine.Quaternion(rx, ry, rz, w);
        }
        catch (Exception e)
        {
            Debug.LogError($"Error extracting rotation: {e.Message}");
            return UnityEngine.Quaternion.identity;
        }
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

    private void OnDestroy()
    {
        isRunning = false;
        consumerThread?.Join();
        consumer?.Close();
        consumer?.Dispose();
    }
}
