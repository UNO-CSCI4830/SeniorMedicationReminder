
medications = [
    {
        "name": "Sample Medication A",
        "dosage": "1 tablet",
        "time": "8:00 AM"
    },
    {
        "name": "Sample Medication B",
        "dosage": "2 tablets",
        "time": "6:00 PM"
    }
]

print("My Medication Reminder")
print("----------------------")

for medication in medications:
    print("Medication:", medication["name"])
    print("Dosage:", medication["dosage"])
    print("Scheduled time:", medication["time"])
    print()

print("Add a New Medication")
print("--------------------")

name = input("Enter medication name: ")
dosage = input("Enter dosage: ")
time = input("Enter reminder time: ")

new_medication = {
    "name": name,
    "dosage": dosage,
    "time": time
}

medications.append(new_medication)

print("\nMedication added!")
print("Medication:", new_medication["name"])
print("Dosage:", new_medication["dosage"])
print("Scheduled time:", new_medication["time"])

