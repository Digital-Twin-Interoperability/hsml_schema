#include "unrealCadreProduicer.h"
#include "Engine/Engine.h"
#include "Misc/FileHelper.h"
#include "Misc/Paths.h"
#include "Json.h"
#include "HAL/PlatformFilemanager.h"

// Sets default values
AunrealCadreProduicer::AunrealCadreProduicer()
{
	// Set this actor to call Tick() every frame.
	PrimaryActorTick.bCanEverTick = true;
}

// Called when the game starts or when spawned
void AunrealCadreProduicer::BeginPlay()
{
	Super::BeginPlay();
}

// Called every frame
void AunrealCadreProduicer::Tick(float DeltaTime)
{
	Super::Tick(DeltaTime);

	// Get actor position and rotation (as Quaternion)
	FVector ActorLocation = GetActorLocation();
	FQuat ActorRotation = GetActorQuat();

	// Write the data to the JSON file
	WriteDataToJson(ActorLocation, ActorRotation);
}

// Helper function to write data to a JSON file
void AunrealCadreProduicer::WriteDataToJson(const FVector& Position, const FQuat& Rotation)
{
	// Get current date and time
	FDateTime Now = FDateTime::Now();
	FString DateCreated = Now.ToString(TEXT("%m-%d-%y"));
	FString DateModified = Now.ToString(TEXT("%m-%d-%y"));

	// Create a JSON object
	TSharedPtr<FJsonObject> JsonObject = MakeShareable(new FJsonObject());
	JsonObject->SetStringField(TEXT("@context"), TEXT("https://digital-twin-interoperability.github.io/hsml-schema-context/hsml.jsonld"));
	JsonObject->SetStringField(TEXT("@type"), TEXT("Agent"));
	JsonObject->SetStringField(TEXT("name"), TEXT("unrealActor"));
	JsonObject->SetStringField(TEXT("swid"), TEXT("did:key:generate-unrealActor")); // placeholder must be modified

	// Identifier with a unique value
	TSharedPtr<FJsonObject> Identifier = MakeShareable(new FJsonObject());
	Identifier->SetStringField(TEXT("@type"), TEXT("PropertyValue"));
	Identifier->SetStringField(TEXT("propertyID"), TEXT("schema_id"));
	Identifier->SetStringField(TEXT("value"), TEXT("unrealActor-001"));
	JsonObject->SetObjectField(TEXT("identifier"), Identifier);

	// URL, creator, and other metadata
	JsonObject->SetStringField(TEXT("url"), TEXT("objectLink"));
	TSharedPtr<FJsonObject> Creator = MakeShareable(new FJsonObject());
	Creator->SetStringField(TEXT("@type"), TEXT("Person"));
	Creator->SetStringField(TEXT("name"), TEXT("Jared Carrillo"));
	JsonObject->SetObjectField(TEXT("creator"), Creator);
	JsonObject->SetStringField(TEXT("dateCreated"), DateCreated);
	JsonObject->SetStringField(TEXT("dateModified"), DateModified);
	JsonObject->SetStringField(TEXT("encodingFormat"), TEXT("application/x-obj"));
	JsonObject->SetStringField(TEXT("contentUrl"), TEXT("https://example.com/models/3dmodel-001.obj"));
	JsonObject->SetStringField(TEXT("platform"), TEXT("Unreal Engine"));
	TSharedPtr<FJsonObject> SpaceLocation = MakeShareable(new FJsonObject());
	SpaceLocation->SetStringField(TEXT("@type"), TEXT("Hyperspace"));
	SpaceLocation->SetStringField(TEXT("name"), TEXT("Moon"));
	JsonObject->SetObjectField(TEXT("spaceLocation"), SpaceLocation);
	JsonObject->SetStringField(TEXT("additionalType"), TEXT("https://schema.org/CreativeWork"));

	// Position array
	TArray<TSharedPtr<FJsonValue>> PositionArray;

	TSharedPtr<FJsonObject> XCoord = MakeShareable(new FJsonObject());
	XCoord->SetStringField(TEXT("name"), TEXT("xCoordinate"));
	XCoord->SetNumberField(TEXT("value"), Position.X * 0.01);  // Adjust back to original scale
	PositionArray.Add(MakeShareable(new FJsonValueObject(XCoord)));
	TSharedPtr<FJsonObject> YCoord = MakeShareable(new FJsonObject());
	YCoord->SetStringField(TEXT("name"), TEXT("yCoordinate"));
	YCoord->SetNumberField(TEXT("value"), Position.Y * -0.01);  // Adjust back to original scale
	PositionArray.Add(MakeShareable(new FJsonValueObject(YCoord)));
	TSharedPtr<FJsonObject> ZCoord = MakeShareable(new FJsonObject());
	ZCoord->SetStringField(TEXT("name"), TEXT("zCoordinate"));
	ZCoord->SetNumberField(TEXT("value"), Position.Z * 0.01);  // Adjust back to original scale
	PositionArray.Add(MakeShareable(new FJsonValueObject(ZCoord)));

	JsonObject->SetArrayField(TEXT("position"), PositionArray);

	// Rotation array
	TArray<TSharedPtr<FJsonValue>> RotationArray;

	TSharedPtr<FJsonObject> RX = MakeShareable(new FJsonObject());
	RX->SetStringField(TEXT("name"), TEXT("rx"));
	RX->SetNumberField(TEXT("value"), Rotation.X);
	RotationArray.Add(MakeShareable(new FJsonValueObject(RX)));
	TSharedPtr<FJsonObject> RY = MakeShareable(new FJsonObject());
	RY->SetStringField(TEXT("name"), TEXT("ry"));
	RY->SetNumberField(TEXT("value"), Rotation.Y);
	RotationArray.Add(MakeShareable(new FJsonValueObject(RY)));
	TSharedPtr<FJsonObject> RZ = MakeShareable(new FJsonObject());
	RZ->SetStringField(TEXT("name"), TEXT("rz"));
	RZ->SetNumberField(TEXT("value"), Rotation.Z);
	RotationArray.Add(MakeShareable(new FJsonValueObject(RZ)));
	TSharedPtr<FJsonObject> RW = MakeShareable(new FJsonObject());
	RW->SetStringField(TEXT("name"), TEXT("w"));
	RW->SetNumberField(TEXT("value"), Rotation.W);
	RotationArray.Add(MakeShareable(new FJsonValueObject(RW)));

	JsonObject->SetArrayField(TEXT("rotation"), RotationArray);

	// Additional properties (e.g., scale)
	TArray<TSharedPtr<FJsonValue>> AdditionalProperties;

	TSharedPtr<FJsonObject> Scale = MakeShareable(new FJsonObject());
	Scale->SetStringField(TEXT("name"), TEXT("scale"));
	Scale->SetNumberField(TEXT("value"), ScaleValue);  // Replace with actual scale value
	AdditionalProperties.Add(MakeShareable(new FJsonValueObject(Scale)));

	JsonObject->SetArrayField(TEXT("additionalProperty"), AdditionalProperties);


	// Description
	JsonObject->SetStringField(TEXT("description"), TEXT("Unreal engine object"));

	// Write the JSON data to file
	FString FilePath = TEXT("C:\\Users\\Jared\\Desktop\\kafkaUnrealProducer.json");
	FString OutputString;

	// Convert the JSON object to string
	TSharedRef<TJsonWriter<>> JsonWriter = TJsonWriterFactory<>::Create(&OutputString);
	if (FJsonSerializer::Serialize(JsonObject.ToSharedRef(), JsonWriter))
	{
		// Overwrite the file with the new data
		FFileHelper::SaveStringToFile(OutputString, *FilePath);
	}
	else
	{
		UE_LOG(LogTemp, Error, TEXT("Failed to serialize JSON!"));
	}
}
