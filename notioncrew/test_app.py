import streamlit as st
import sys
import time
from io import StringIO


class StreamlitLogger:
    def __init__(self, container):
        self.output = StringIO()
        self.container = container

    def write(self, message):
        # Write the message to the StringIO buffer
        self.output.write(message)
        # Update the container's content with the current output
        self.container.text_area("Terminal Output", self.output.getvalue(), height=400)

    def flush(self):
        # Required for compatibility with `sys.stdout`
        pass


# Streamlit app logic
def main():
    st.title("Streamlit Terminal Output Example")

    # Create a placeholder container for the terminal output
    output_container = st.empty()

    # Create a logger instance and pass the container
    logger = StreamlitLogger(output_container)

    # Redirect stdout to the custom logger
    sys.stdout = logger

    # Example of writing to the terminal (which will now show in Streamlit)
    st.write("Click the button to generate output.")
    if st.button("Generate Output"):
        for i in range(5):
            print(f"Processing step {i + 1}/5...")
            time.sleep(1)  # Simulate some work

    # Reset stdout when done
    sys.stdout = sys.__stdout__


if __name__ == "__main__":
    main()
