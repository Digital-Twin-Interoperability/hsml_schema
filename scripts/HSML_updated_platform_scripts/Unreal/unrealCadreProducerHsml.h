#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "unrealCadreProduicer.generated.h"

UCLASS()
class KAFKA16_API AunrealCadreProduicer : public AActor
{
	GENERATED_BODY()

public:
	// Sets default values for this actor's properties
	AunrealCadreProduicer();

protected:
	// Called when the game starts or when spawned
	virtual void BeginPlay() override;

public:
	// Called every frame
	virtual void Tick(float DeltaTime) override;

private:
	// Helper function to write data to a JSON file
	void WriteDataToJson(const FVector& Position, const FQuat& Rotation);
};
