a,b = 20,3
print(f"floor division: {a // b}")
print (f"Modulus: {a % b}")
print (f"power operator: {a ** b}")

str1 = "Hello"
str2 = "World"
print (f"Concatenation: {str1 + str2}")

text = "Python Programming"
print (f"String slicing: {text[0:6]}")
print ("Python" in text)
print("text split: ", text.split())

fruits = ["apple", "banana", "cherry"]
print (fruits)  # Accessing first element
popped_fruit = fruits.pop()  # Removing last element
print (f"Popped fruit: {popped_fruit}")
print (f"Remaining fruits: {fruits}")

# Tuple methods
colors = ("red", "green", "blue", "red")
print(colors.count("red"))  # Output: 2
print(colors.index("green")) # Output: 1

person = {
    "name": "Alice",
    "age": 30,
    "city": "New York"
}
print (person)
print(person["age"]) # Output: 30
print(person["city"]) # Output: New York