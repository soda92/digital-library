import socket
import sys
import threading
import time

# --- Helper Functions for SIP2 Message Handling ---


def calculate_checksum(msg_data):
    """Calculates a very basic checksum for demo purposes.
    Real SIP2 checksum is more complex (sum of ASCII values modulo 65536, then 2's complement).
    For a proper demo, you might just return '0000' or implement the real algorithm.
    """
    s = sum(ord(c) for c in msg_data)
    # This is a simplified checksum, not the full SIP2 standard.
    # For a robust server, refer to the SIP2 spec for checksum calculation.
    return str(s % 10000).zfill(4)  # Just summing ASCII values and taking last 4 digits


def build_sip2_message(message_code, fields="", sequence_number=0):
    """Builds a complete SIP2 message with length prefix, seq num, and checksum."""
    # The message data part without length prefix, seq num, or checksum
    msg_body = f"{message_code}{fields}"

    # Calculate checksum for the msg_body + seq_num part
    # Note: SIP2 checksum includes the sequence number, but *not* the checksum itself or length.
    # We use a placeholder for now, actual SIP2 checksum is more involved.
    calculated_cs = calculate_checksum(msg_body + str(sequence_number))  # Simplified!

    # Assemble the full message before length prefix
    full_msg_without_len = f"{msg_body}{sequence_number}{calculated_cs}\r"

    # Calculate total length including the 4-digit length prefix itself and the final CR
    total_length = len(full_msg_without_len) + 4

    # Format the length prefix
    len_prefix = str(total_length).zfill(4)

    # Combine everything
    final_message = f"{len_prefix}{full_msg_without_len}"
    return final_message


def parse_sip2_message(raw_message):
    """Parses a raw SIP2 message received from the client."""
    if (
        not raw_message or len(raw_message) < 5
    ):  # Min length: 4 for len + 1 for cmd code
        return None, "Too short"

    try:
        length_str = raw_message[:4]
        declared_length = int(length_str)

        # Check if the message is fully received
        if len(raw_message) < declared_length:
            return None, "Partial message"

        # Extract the actual message content based on declared length
        message_content = raw_message[
            4 : declared_length - 1
        ]  # Exclude len prefix and CR

        # Verify CR terminator
        if raw_message[declared_length - 1] != "\r":
            return None, "Missing CR terminator"

        message_code = message_content[:2]
        fields_part = message_content[2:-5]  # Exclude code, seq, checksum
        sequence_number = message_content[-5]  # The single digit sequence number
        checksum = message_content[-4:]  # The 4-digit checksum

        # For a demo, we might skip full checksum verification, but it's crucial in real systems.

        return {
            "raw": raw_message.strip(),
            "length": declared_length,
            "code": message_code,
            "fields": fields_part,
            "sequence_number": sequence_number,
            "checksum": checksum,
        }, None

    except ValueError:
        return None, "Invalid length prefix"
    except Exception as e:
        return None, f"Parsing error: {e}"


# --- Mock SIP2 Server Logic ---


class MockSIP2Server:
    def __init__(self, host="127.0.0.1", port=6000):
        self.host = host
        self.port = port
        self.running = False
        self.sequence_counter = 0  # For generating responses

    def _handle_client(self, conn, addr):
        print(f"[Client Connected] {addr}")
        buffer = ""
        while self.running:
            try:
                data = conn.recv(4096).decode("ascii")
                if not data:
                    break  # Client disconnected

                buffer += data

                # Look for a complete message
                while "\r" in buffer:
                    cr_index = buffer.find("\r")
                    potential_message = buffer[: cr_index + 1]

                    parsed_msg, error = parse_sip2_message(potential_message)

                    if error == "Partial message":
                        # Not enough data for declared length, wait for more
                        break
                    elif error:
                        print(
                            f"[{addr}] Error parsing message: {error}. Raw: {potential_message.strip()}"
                        )
                        buffer = buffer[cr_index + 1 :]  # Skip malformed message
                        continue

                    print(f"[{addr}] Received: {parsed_msg['raw']}")

                    # Process the message and send a response
                    response = self._generate_response(parsed_msg)
                    if response:
                        print(f"[{addr}] Sending: {response.strip()}")
                        conn.sendall(response.encode("ascii"))

                    # Remove processed message from buffer
                    buffer = buffer[cr_index + 1 :]

            except ConnectionResetError:
                print(f"[Client Disconnected] {addr}")
                break
            except Exception as e:
                print(f"[{addr}] An error occurred: {e}")
                break
        conn.close()
        print(f"[Client Handler Closed] {addr}")

    def _generate_response(self, parsed_msg):
        """Generates a mock SIP2 response based on the incoming message."""
        command = parsed_msg["code"]
        client_seq_num = parsed_msg[
            "sequence_number"
        ]  # Use client's sequence number for response (AY)

        # Increment server's internal sequence counter for its own messages
        self.sequence_counter = (self.sequence_counter + 1) % 10

        response_fields = ""
        response_code = ""

        if command == "93":  # Login Request
            # 94 - Login Response
            # Success: '1' or '0' for fail. 'AO' for patron identifier.
            response_code = "94"
            response_fields = "1"  # Login successful

        elif command == "11":  # Checkout Request
            # 12 - Checkout Response
            # Success: '1' or '0' for fail.
            # 'AA' Patron Identifier, 'AB' Item Identifier
            response_code = "12"
            response_fields = "1"  # Checkout successful
            # Example: 121AOpatron123|ABitem456|...

        elif command == "09":  # Checkin Request
            # 10 - Checkin Response
            # Success: '1' or '0' for fail.
            # 'AB' Item Identifier
            response_code = "10"
            response_fields = "1"  # Checkin successful
            # Example: 101ABitem456|...

        elif command == "23":  # Patron Status Request
            # 24 - Patron Status Response
            response_code = "24"
            # Example: 24100NImy_patron_name|AAmy_patron_id|BLsome_institution|...
            response_fields = (
                "100NIName, My Patron|AA"
                + parsed_msg["fields"].split("AA")[-1].split("|")[0]
                + "|"
            )

        else:
            print(f"Warning: Unhandled SIP2 command: {command}")
            # Send an error or unsupported message response if needed (e.g., 99 - Error)
            return None

        # Build and return the complete SIP2 response message
        return build_sip2_message(response_code, response_fields, client_seq_num)

    def start(self):
        self.running = True
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(
            socket.SOL_SOCKET, socket.SO_REUSEADDR, 1
        )  # Allow reuse of address

        try:
            self.server_socket.bind((self.host, self.port))
            self.server_socket.listen(5)
            print(f"Mock SIP2 Server listening on {self.host}:{self.port}")
            print("Waiting for client connections...")

            while self.running:
                conn, addr = self.server_socket.accept()
                client_thread = threading.Thread(
                    target=self._handle_client, args=(conn, addr)
                )
                client_thread.daemon = (
                    True  # Allow main program to exit even if threads are running
                )
                client_thread.start()

        except socket.error as e:
            print(f"Could not start server: {e}")
            self.running = False
        except KeyboardInterrupt:
            print("Server shutting down due to KeyboardInterrupt.")
        finally:
            self.stop()

    def stop(self):
        self.running = False
        if self.server_socket:
            self.server_socket.close()
            print("Mock SIP2 Server stopped.")


if __name__ == "__main__":
    server = MockSIP2Server("127.0.0.1", 6000)
    server.start()
