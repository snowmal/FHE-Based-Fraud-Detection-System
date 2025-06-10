from carol_listener import process

def carol_entry(event, context):
    print("[CAROL] Triggered Cloud Function")
    process()
