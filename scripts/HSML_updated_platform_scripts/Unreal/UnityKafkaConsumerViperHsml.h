#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "Math/Quat.h"  // Include Quat here
#include "UnityKafkaConsumerViper.generated.h"

// Forward declaration to avoid direct dependency
class AActor;

UCLASS()
class KAFKA16_API AUnityKafkaConsumerViper : public AActor
{
    GENERATED_BODY()

public:
    // Sets default values for this actor's properties
    AUnityKafkaConsumerViper();

protected:
    // Called when the game starts or when spawned
    virtual void BeginPlay() override;

public:
    // Called every frame
    virtual void Tick(float DeltaTime) override;

private:
    // Method to read and update actor from JSON file
    void ReadAndUpdateActorFromJson();

    // The path to the JSON file
    FString JsonFilePath = "C:/Users/Pard1/Desktop/kafkaUnrealConsumer_2_hsml.json";

    // The actor's new position and rotation (using FQuat for quaternion rotation)
    FVector NewPosition;
    FQuat RotationQuat;

    // Time tracking for reading the file 30 times per second
    float TimeSinceLastRead;
    float ReadInterval;

    // A reference to the actor to move in the scene
    UPROPERTY(EditAnywhere)
    AActor* TargetActor;  // You can assign this in the editor or through code

};
