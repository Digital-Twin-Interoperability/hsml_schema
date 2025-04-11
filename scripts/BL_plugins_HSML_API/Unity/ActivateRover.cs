using UnityEngine;

public class ActivateRover : MonoBehaviour
{
    public GameObject targetObject; // The object to enable/disable physics components on
    public static bool inControl = false; // Static variable to allow access from other scripts

    private BoxCollider boxCollider;
    private Rigidbody rb;

    // Scripts to enable/disable
    public MonoBehaviour scriptToDisable;
    public MonoBehaviour scriptToEnable;

    private bool switchActivated = false; // To track if the switch has already been made

    void Start()
    {
        if (targetObject != null)
        {
            // Get or add BoxCollider and Rigidbody
            boxCollider = targetObject.GetComponent<BoxCollider>();
            if (boxCollider == null)
            {
                boxCollider = targetObject.AddComponent<BoxCollider>();
                Debug.Log("BoxCollider added to " + targetObject.name);
            }

            rb = targetObject.GetComponent<Rigidbody>();
            if (rb == null)
            {
                rb = targetObject.AddComponent<Rigidbody>();
                Debug.Log("Rigidbody added to " + targetObject.name);
            }

            // Set the BoxCollider size
            boxCollider.size = new Vector3(16.4f, 7f, 15.8f);
            Debug.Log("BoxCollider size set to (16.4, 7, 15.8)");

            // Initially disable components and set inControl to false
            DisablePhysics();
            inControl = false;

            // Ensure the scripts are in the correct initial state
            if (scriptToDisable != null)
            {
                scriptToDisable.enabled = true;
            }
            if (scriptToEnable != null)
            {
                scriptToEnable.enabled = false;
            }
        }
        else
        {
            Debug.LogWarning("Target Object is not assigned in the Inspector!");
        }
    }

    void OnTriggerEnter(Collider other)
    {
        if (other.CompareTag("Player") && !switchActivated) // Only allow switching once
        {
            Debug.Log("The PLAYER has entered the trigger! Enabling physics.");
            EnablePhysics();
            inControl = true; // Set inControl to true when the player enters the trigger

            // Enable the new script and disable the old one
            if (scriptToDisable != null)
            {
                scriptToDisable.enabled = false;
                Debug.Log(scriptToDisable.GetType().Name + " disabled.");
            }
            if (scriptToEnable != null)
            {
                scriptToEnable.enabled = true;
                Debug.Log(scriptToEnable.GetType().Name + " enabled.");
            }

            // Mark the switch as activated so it won't revert or change again
            switchActivated = true;
        }
    }

    void EnablePhysics()
    {
        if (boxCollider != null)
        {
            boxCollider.enabled = true;
        }
        if (rb != null)
        {
            rb.isKinematic = false; // Enable physics interactions
        }
    }

    void DisablePhysics()
    {
        if (boxCollider != null)
        {
            boxCollider.enabled = false;
        }
        if (rb != null)
        {
            rb.isKinematic = true; // Disable physics interactions
        }
    }
}
