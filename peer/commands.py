import os
import utils
import records
import json
import time


def get_rfc_dir():
    rfc_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "rfc")
    if not os.path.exists(rfc_dir):
        os.makedirs(rfc_dir)
    return rfc_dir


def get_rfc_path(rfc_number):
    return os.path.join(get_rfc_dir(), rfc_number + ".txt")


def read_rfc_metadata():
    utils.Logging.debug("Entering peer.read_rfc_metadata")
    metadata_file = os.path.join(get_rfc_dir(), "metadata.json")
    # Load metadata.json
    metadata = None
    try:
            try:
                f = open(metadata_file, "r")
                metadata = json.load(f)
                f.close()
            except ValueError as err:
                utils.Logging.info("Could not load %s. %s" % (metadata_file, err))
    except IOError:
        utils.Logging.info("No %s found" % metadata_file)
    utils.Logging.debug("Exiting peer.read_rfc_metadata")
    return metadata


def update_rfc_metadata(number, title):
    utils.Logging.debug("Entering peer.update_rfc_metadata")
    new_data = {"number": str(number), "title": title}
    metadata_file = os.path.join(get_rfc_dir(), "metadata.json")
    try:
        metadata = read_rfc_metadata()
        if metadata and isinstance(metadata, dict):
            metadata["rfcs"].append(new_data)
        else:
            metadata = {"rfcs": []}
            metadata["rfcs"].append(new_data)
        f = open(metadata_file, "w")
        json.dump(metadata, f)
        f.close()
        updated = True
    except BaseException as err:
        updated = False
        utils.Logging.debug(err)
    utils.Logging.debug("Exiting peer.update_rfc_metadata")
    return updated


def build_rfc_index():
    utils.Logging.debug("Entering peer.build_rfc_index")
    metadata = read_rfc_metadata()
    head = None
    if metadata:
        for obj in metadata["rfcs"]:
            rfc = records.RFC("localhost", obj["number"], obj["title"])
            rfc_node = records.Node(rfc)
            head = rfc_node.insert(head)
    else:
        utils.Logging.info("Metadata empty, no records of local rfcs found")
    utils.Logging.debug("Exiting peer.build_rfc_index")
    return head


def create_data_field(cookie, port):
    return {"cookie": cookie, "port": port}


def periodic_ttl_reduction(head, last_time_updated):
    if head:
        current_time = int(time.time())
        decrement_value = current_time - last_time_updated
        utils.Logging.info("TTL reduction by %s" % decrement_value)
        ptr = head
        while ptr:
            ptr.rfc.decrement_ttl(decrement_value)
            ptr = ptr.nxt


def check_rfc_metadata(rfc_number):
    utils.Logging.debug("Entering peer.check_rfc_metadata")
    metadata = read_rfc_metadata()
    if metadata and metadata["rfcs"]:
        for rfc in metadata["rfcs"]:
            if rfc["number"] == rfc_number:
                return get_rfc_path(rfc_number)
    utils.Logging.debug("Exiting peer.check_rfc_metadata")
    return None


# Query a peer for its RFC index
def get_rfc_index_from_peer(hostname, port):
    utils.Logging.debug("Entering peer.get_rfc_index_from_peer")
    peer_rfc_index_head = None
    sock = utils.send_request(hostname, port, "RFCQuery", {})
    response = utils.accept_response(sock)
    if response.status == "200":
        peer_rfc_index_head = records.decode_rfc_list(hostname, response.data)
    utils.Logging.debug("Exiting peer.get_rfc_index_from_peer")
    return peer_rfc_index_head


# Get RFC from a peer
def get_rfc_from_peer(peer_ip, peer_port, rfc_number):
    utils.Logging.debug("Entering peer.get_rfc_from_peer")
    sock = utils.send_request(peer_ip, peer_port, "GetRFC", {"rfc": rfc_number})
    rfc_path = get_rfc_path(rfc_number)
    downloaded = utils.accept_rfc(sock, rfc_path)
    if not downloaded:
        rfc_path = None
    utils.Logging.debug("Exiting peer.get_rfc_from_peer")
    return rfc_path
