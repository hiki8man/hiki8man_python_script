from pathlib import Path
from fastmcp import FastMCP
from fastmcp.server.providers import FileSystemProvider

server: FastMCP = FastMCP(
    name="osu-info",
    providers=[FileSystemProvider(Path(__file__).joinpath("tools"))]
)

if __name__ == "__main__":
    server.run()