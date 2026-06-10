from backend.services.ojs_scanner import OjsScannerAgent, OjsScannerAgentConfig


def main():
    agent = OjsScannerAgent(OjsScannerAgentConfig())
    agent.run_forever()


if __name__ == "__main__":
    main()
