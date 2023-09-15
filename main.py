
import open3d as o3d
from plyfile import PlyData, PlyElement
import numpy as np
import os
import re

file_dir = "CameraMatrix"
output_dir = 'CameraMatrixOutput'
json_name = "groups.json"
point_array_global = []
point_arrays = []
label_array_global = []
label_arrays = []
unique_label_array_global = []
unique_label_arrays = []
color_array_global = []
color_arrays = []

def split_camel_case(s):
    """Splits a CamelCase string into a list of words."""
    return re.findall(r'[A-Z](?:[a-z]+|[A-Z]*(?=[A-Z]|$))', s)


def largest_word(s):
    """Return the largest word in a string split by underscores or from a CamelCase, excluding words with numbers."""
    words = s.split("_")
    expanded_words = []

    for word in words:
        if re.search(r'([A-Z][a-z]+)', word):  # If the word contains CamelCase
            expanded_words.extend(split_camel_case(word))
        else:
            expanded_words.append(word)

    # Filter out words containing any numeric character
    non_numeric_words = [word for word in expanded_words if not re.search(r'\d', word)]

    # If there are any non-numeric words, find the largest among them
    if non_numeric_words:
        return max(non_numeric_words, key=len)

    # If there are no non-numeric words, return an empty string (or you could handle this differently)
    return ""


def group_by_largest_word(strings):
    """Group list of strings by the largest underscore-separated word."""
    # Sort strings by largest word
    sorted_strings = sorted(strings, key=largest_word)

    # Group strings by largest word
    groups = {}
    for s in sorted_strings:
        key = largest_word(s)
        if key in groups:
            groups[key].append(s)
        else:
            groups[key] = [s]

    return groups


def parse_files(directory):
    filenames = os.listdir(directory)
    for file_path in filenames:
        with open(os.path.join(file_dir, file_path), "r") as file:
            file_contents = file.read()

        points = file_contents.split("\\n")

        point_array = []
        color_array = []
        label_array = []

        for point in points:
            pairs = point.split()
            x = None
            y = None
            z = None
            r = None
            g = None
            b = None
            label = None

            for pair in pairs:
                key, value = pair.split('=')
                if key == 'X':
                    x = float(value)
                elif key == 'Y':
                    y = float(value)
                elif key == 'Z':
                    z = float(value)
                elif key == 'R':
                    r = float(value)
                elif key == 'G':
                    g = float(value)
                elif key == 'B':
                    b = float(value)
                elif key == 'Label':
                    label = value

            if x is not None:
                point_array.append([x, y, z])
            elif r is not None:
                color_array.append([r, g, b])
                # print([r, g, b])
            elif label is not None:
                label_array.append(label)

        point_array_global.extend(point_array)
        point_arrays.append(point_array)

        label_array_global.extend(label_array)
        label_arrays.append(label_array)

        color_array_global.extend(color_array)
        color_arrays.append(color_array)

def generate_unique_labels(label_array):
    unique_labels = list(set(label_array))


    result = group_by_largest_word(unique_labels)
    for key, group in result.items():
        print(f"{key}: {group}")


    # print(label_array)
    for i, label in enumerate(label_array):
        key = largest_word(label)
        if key in result:
            # print(label_array[i])
            # print(key)

            label_array[i] = key

    unique_labels = list(set(label_array))
    print(unique_labels)
    return label_array
    # unique_label_array_global.extend(unique_labels)
    # unique_label_arrays.append(unique_labels)
    # print(unique_labels)

def generate_label_colors(unique_labels, label_array):
    string_to_int = {string: i for i, string in enumerate(unique_labels)}
    label_numbers = np.array([string_to_int[label] for label in label_array])
    highest = max(label_numbers)
    label_colors = np.random.rand(highest + 1, 3)
    label_colors_array = np.array([label_colors[i] for i in label_numbers])

def map_labels_to_integers(label_array):
    unique_labels = list(set(label_array))
    label_to_int = {label: i for i, label in enumerate(unique_labels)}
    int_labels = [label_to_int[label] for label in label_array]
    return int_labels

def save_point_cloud_with_labels_and_colors(point_array, label_array, color_array, filename):

    point_array = np.array(point_array)
    label_array = np.array(label_array)
    color_array = np.array(color_array)
    if len(point_array) != len(label_array) or len(point_array) != len(color_array):
        print(len(point_array))
        print(len(label_array))
        print(len(color_array))
        raise ValueError("Point array, label array, and color array must have the same length.")

    # Create a NumPy array to hold the point cloud, labels, and colors
    vertex_data = np.zeros(len(point_array), dtype=[('x', 'f4'), ('y', 'f4'), ('z', 'f4'),
                                                    ('label', 'i4'), ('red', 'u1'), ('green', 'u1'), ('blue', 'u1')])

    vertex_data['x'] = point_array[:, 0]
    vertex_data['y'] = point_array[:, 1]
    vertex_data['z'] = point_array[:, 2]
    # print(label_array)
    vertex_data['label'] = label_array
    vertex_data['red'] = color_array[:, 0]*255
    vertex_data['green'] = color_array[:, 1]*255
    vertex_data['blue'] = color_array[:, 2]*255

    # Create the PlyElement instance
    vertex_element = PlyElement.describe(vertex_data, 'vertex')

    # Create the PlyData instance and write to file
    ply_data = PlyData([vertex_element])
    ply_data.write(filename)

# Main code

if not os.path.exists(output_dir):
    os.makedirs(output_dir)

parse_files(file_dir)

# Generate individual ply scans
for i in range(0, len(point_arrays)):
    unique_label_array = generate_unique_labels(label_arrays[i])
    int_labels = map_labels_to_integers(unique_label_array)
    filename = f"pointcloud_{i}.ply"
    filepath = os.path.join(output_dir, filename)
    save_point_cloud_with_labels_and_colors(point_arrays[i], int_labels, color_arrays[i], filepath)

# Generate global scan
unique_label_array_global = generate_unique_labels(label_array_global)
int_labels = map_labels_to_integers(unique_label_array_global)
for label_array in label_arrays:
    unique_label_arrays.append(generate_unique_labels(label_array))

filepath = os.path.join(output_dir, "global.ply")
save_point_cloud_with_labels_and_colors(point_array_global, int_labels, color_array_global, filepath)


# Display Global PLY
pcd = o3d.io.read_point_cloud(filepath)
o3d.visualization.draw_geometries([pcd])
