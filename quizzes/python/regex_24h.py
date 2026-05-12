import re

pattern = re.compile(r'(?:[01]{1}[0-9]{1}|2{1}[0-3]{1}):[0-5]{1}[0-9]{1}')

sample_text = "The meeting is at 20:22, but the gym opens at 06:30. Skip 25:00."
matches = pattern.findall(sample_text)

print(matches)

sample_text = 'time-is-20:22-now'
matches = pattern.findall(sample_text)

print(matches)

