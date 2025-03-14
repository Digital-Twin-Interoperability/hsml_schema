#include "omniKafkaConsumerCadre.h"
#include "Misc/FileHelper.h"
#include "Misc/Paths.h"
#include "Json.h"
#include "HAL/PlatformProcess.h"  // For FPlatformProcess::Sleep
#include "Math/Quat.h"  // Correct header for FQuat

// Sets default values
AomniKafkaConsumerCadre::AomniKafkaConsumerCadre()
{
	// Set this actor to call Tick() every frame. You can turn this off to improve performance if you don't need it.
	PrimaryActorTick.bCanEverTick = true;

	// Initialize the counter and time interval for reading the JSON
	TimeSinceLastRead = 0.0f;
	ReadInterval = 1.0f / 30.0f;  // 30 times per second (approximately 0.0333 seconds per read)
}

// Called when the game starts or when spawned
void AomniKafkaConsumerCadre::BeginPlay()
{
	Super::BeginPlay();

	// Initial test of JSON reading and actor movement
	ReadAndUpdateActorFromJson();

	// Log initial position and rotation
	UE_LOG(LogTemp, Warning, TEXT("Initial Actor Position: %s"), *NewPosition.ToString());
}

// Called every frame
void AomniKafkaConsumerCadre::Tick(float DeltaTime)
{
	Super::Tick(DeltaTime);

	// Accumulate the time since the last read
	TimeSinceLastRead += DeltaTime;

	// Check if it's time to read the file (30 times per second)
	if (TimeSinceLastRead >= ReadInterval)
	{
		// Reset the counter and read the JSON
		TimeSinceLastRead = 0.0f;
		ReadAndUpdateActorFromJson();
	}

	// Log the actor's current position for debugging
	FVector CurrentPosition = GetActorLocation();
	UE_LOG(LogTemp, Warning, TEXT("Current Actor Position: %s"), *CurrentPosition.ToString());

	// If the target actor exists, update its position and rotation
	if (TargetActor)
	{
		TargetActor->SetActorLocation(NewPosition);
		TargetActor->SetActorRotation(RotationQuat);  // Apply quaternion-based rotation
	}
}

void AomniKafkaConsumerCadre::ReadAndUpdateActorFromJson()
{
	FString JsonString;
	bool bFileLoaded = false;
	int32 MaxRetries = 5;  // Max number of retry attempts
	int32 RetryCount = 0;

	// Retry loading the file if it's locked or in use
	while (!bFileLoaded && RetryCount < MaxRetries)
	{
		// Attempt to load the JSON file
		if (FFileHelper::LoadFileToString(JsonString, *JsonFilePath))
		{
			bFileLoaded = true;  // Successfully loaded the file
			UE_LOG(LogTemp, Warning, TEXT("Successfully loaded JSON file on attempt %d"), RetryCount + 1);
		}
		else
		{
			RetryCount++;
			UE_LOG(LogTemp, Warning, TEXT("Attempt %d to load the JSON file failed. Retrying..."), RetryCount);
			FPlatformProcess::Sleep(0.5f);  // Wait for 0.5 seconds before retrying
		}
	}

	if (!bFileLoaded)
	{
		UE_LOG(LogTemp, Error, TEXT("Failed to load the JSON file after %d attempts."), MaxRetries);
		return;  // Exit if the file could not be loaded after retries
	}

	// Log the content of the loaded JSON file for debugging
	UE_LOG(LogTemp, Warning, TEXT("Loaded JSON content: %s"), *JsonString);

	// Parse the JSON string
	TSharedRef<TJsonReader<TCHAR>> JsonReader = TJsonReaderFactory<TCHAR>::Create(JsonString);
	TSharedPtr<FJsonObject> JsonObject;

	if (FJsonSerializer::Deserialize(JsonReader, JsonObject))
	{
    	UE_LOG(LogTemp, Warning, TEXT("JSON deserialization successful"));

    	// Get the "position" array
    	const TArray<TSharedPtr<FJsonValue>>* PositionArray;
		if (JsonObject->TryGetArrayField(TEXT("position"), PositionArray))
		{
			// Loop through each item in the position array
			for (const TSharedPtr<FJsonValue>& PropertyValue : *PositionArray)
			{
				TSharedPtr<FJsonObject> PropertyObject = PropertyValue->AsObject();
				if (PropertyObject.IsValid())
				{
					// Get the "name" field
					FString PropertyName;
					if (PropertyObject->TryGetStringField(TEXT("name"), PropertyName))
					{
						if (PropertyName == TEXT("xCoordinate"))
						{
							NewPosition.X = PropertyObject->GetNumberField(TEXT("value")) * 100; // Multiply by 100
						}
						else if (PropertyName == TEXT("yCoordinate"))
						{
							NewPosition.Y = PropertyObject->GetNumberField(TEXT("value")) * 100; // Multiply by 100
						}
						else if (PropertyName == TEXT("zCoordinate"))
						{
							NewPosition.Z = PropertyObject->GetNumberField(TEXT("value")) * 100; // Multiply by 100
						}
					}
				}
			}
		}
		else
		{
			UE_LOG(LogTemp, Warning, TEXT("No position field found in the JSON."));
		}

		// Get the "rotation" array
		const TArray<TSharedPtr<FJsonValue>>* RotationArray;
		if (JsonObject->TryGetArrayField(TEXT("rotation"), RotationArray))
		{
			for (const TSharedPtr<FJsonValue>& PropertyValue : *RotationArray)
			{
				TSharedPtr<FJsonObject> PropertyObject = PropertyValue->AsObject();
				if (PropertyObject.IsValid())
				{
					FString PropertyName;
					if (PropertyObject->TryGetStringField(TEXT("name"), PropertyName))
					{
						if (PropertyName == TEXT("rx"))
						{
							RotationQuat.X = PropertyObject->GetNumberField(TEXT("value")); // rx component
						}
						else if (PropertyName == TEXT("ry"))
						{
							RotationQuat.Y = PropertyObject->GetNumberField(TEXT("value")); // ry component
						}
						else if (PropertyName == TEXT("rz"))
						{
							RotationQuat.Z = PropertyObject->GetNumberField(TEXT("value")); // rz component
						}
						else if (PropertyName == TEXT("w"))
						{
							RotationQuat.W = PropertyObject->GetNumberField(TEXT("value")); // w component
						}
					}
				}
			}
		}
		else
		{
			UE_LOG(LogTemp, Warning, TEXT("No rotation field found in the JSON."));
		}

		// Get the "additionalProperty" array (now contains "scale")
		const TArray<TSharedPtr<FJsonValue>>* AdditionalProperties;
		if (JsonObject->TryGetArrayField(TEXT("additionalProperty"), AdditionalProperties))
		{
			for (const TSharedPtr<FJsonValue>& PropertyValue : *AdditionalProperties)
			{
				TSharedPtr<FJsonObject> PropertyObject = PropertyValue->AsObject();
				if (PropertyObject.IsValid())
				{
					FString PropertyName;
					if (PropertyObject->TryGetStringField(TEXT("name"), PropertyName))
					{
						if (PropertyName == TEXT("scale"))
						{
							float ScaleValue = PropertyObject->GetNumberField(TEXT("value"));
							UE_LOG(LogTemp, Warning, TEXT("Scale value found: %f"), ScaleValue);
							// Store or use ScaleValue as needed
						}
					}
				}
			}
		}
		else
		{
			UE_LOG(LogTemp, Warning, TEXT("No additionalProperty field found in the JSON."));
		}

		// Log the position and quaternion rotation before applying to the actor
		UE_LOG(LogTemp, Warning, TEXT("New Position: %s"), *NewPosition.ToString());
		UE_LOG(LogTemp, Warning, TEXT("New Rotation (Quat): %s"), *RotationQuat.ToString());
	}
	else
	{
		UE_LOG(LogTemp, Error, TEXT("Failed to deserialize the JSON file."));
	}
}
