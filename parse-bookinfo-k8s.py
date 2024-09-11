import requests
import yaml
import os

# Define the list of YAML URLs
# https://docs.openshift.com/container-platform/4.16/service_mesh/v2x/ossm-create-mesh.html#ossm-tutorial-bookinfo-overview_ossm-create-mesh
# yaml_urls = [
#     "https://raw.githubusercontent.com/Maistra/istio/maistra-2.6/samples/bookinfo/platform/kube/bookinfo.yaml",
#     "https://raw.githubusercontent.com/Maistra/istio/maistra-2.6/samples/bookinfo/networking/bookinfo-gateway.yaml",
#     "https://raw.githubusercontent.com/Maistra/istio/maistra-2.6/samples/bookinfo/networking/destination-rule-all.yaml"
#     # ,    "https://raw.githubusercontent.com/Maistra/istio/maistra-2.6/samples/bookinfo/networking/destination-rule-all-mtls.yaml"
#     # Add more URLs here
# ]
# output_dir = "bookinfo/istio-1.20"



yaml_urls = [
    "https://raw.githubusercontent.com/istio/istio/release-1.20/samples/bookinfo/platform/kube/bookinfo.yaml",
    "https://raw.githubusercontent.com/istio/istio/release-1.20/samples/bookinfo/networking/bookinfo-gateway.yaml",
    "https://raw.githubusercontent.com/istio/istio/release-1.20/samples/bookinfo/networking/destination-rule-all.yaml"
    # Add more URLs here
]
output_dir = "bookinfo/maistra-2.6"


# Create a directory to store the generated files
os.makedirs(output_dir, exist_ok=True)

# Function to create filenames based on resource kind and name
def create_filename(resource):
    kind = resource["kind"].lower()
    name = resource["metadata"]["name"].lower()
    if kind == "service":
        # If it's a service, append the port if available
        ports = resource["spec"].get("ports", [])
        if ports:
            port = ports[0]["port"]
            return f"svc-{name}-{port}.yaml"
    return f"{kind}-{name}.yaml"

# Save each resource in a separate file and log the process
output_files = []

# Loop over each URL and process the YAML file
for yaml_url in yaml_urls:
    # Fetch the YAML content
    response = requests.get(yaml_url)
    bookinfo_yaml = response.text
    
    # Load YAML content as a Python object
    resources = list(yaml.safe_load_all(bookinfo_yaml))
    
    # Keep track of which resources come from each URL
    url_files = []
    
    for resource in resources:
        # Skip None values, which occur when there is an empty '---'
        if resource is None:
            continue
        
        kind = resource["kind"]
        name = resource["metadata"]["name"]
        filename = create_filename(resource)
        filepath = os.path.join(output_dir, filename)
        
        # Log which resource is being processed
        print(f"Processing {kind}: {name}, saving as {filename}")
        
        with open(filepath, 'w') as file:
            # Add "---" to the first line and then dump the YAML content
            file.write("---\n")
            yaml.dump(resource, file)
        
        # Append the filename without the "files/" part to the URL-specific list
        url_files.append(filename)
    
    # Append the files to the main list with a comment for the URL
    output_files.append(f"# Original content: {yaml_url}")
    output_files.extend(url_files)

# Generate kustomization.yaml file
kustomization_path = os.path.join(output_dir, 'kustomization.yaml')
with open(kustomization_path, 'w') as kustomize_file:
    kustomize_file.write("---\n")
    kustomize_file.write("apiVersion: kustomize.config.k8s.io/v1beta1\n")
    kustomize_file.write("kind: Kustomization\n")
    kustomize_file.write("resources:\n")
    for output_file in output_files:
        # If the entry is a URL comment, write it as a comment, otherwise write it as a resource
        if output_file.startswith("#"):
            kustomize_file.write(f"  {output_file}\n")
        else:
            kustomize_file.write(f"  - {output_file}\n")

print(f"Kustomization file created at {kustomization_path}")
