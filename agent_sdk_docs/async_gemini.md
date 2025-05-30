This notebook will show you how to make asynchronous and parallel requests using the Gemini API's Python SDK and Python 3's asyncio standard library.

The examples here run in Google Colab and use the implicit event loop supplied in Colab. You can also run these commands interactively using the asyncio REPL (invoked with python -m asyncio), or you can manage the event loop yourself.


[ ]
%pip install -qU 'google-genai>=1.0.0' aiohttp
Set up your API key
To run the following cell, your API key must be stored it in a Colab Secret named GOOGLE_API_KEY. If you don't already have an API key, or you're not sure how to create a Colab Secret, see the Authentication quickstart for an example.


[ ]
from google.colab import userdata
from google import genai

GOOGLE_API_KEY = userdata.get("GOOGLE_API_KEY")
client = genai.Client(api_key=GOOGLE_API_KEY)
Now select the model you want to use in this guide, either by selecting one in the list or writing it down. Keep in mind that some models, like the 2.5 ones are thinking models and thus take slightly more time to respond (cf. thinking notebook for more details and in particular learn how to switch the thiking off).


[ ]
MODEL_ID = "gemini-2.5-flash-preview-05-20" # @param ["gemini-2.0-flash-lite","gemini-2.0-flash","gemini-2.5-flash-preview-05-20","gemini-2.5-pro-preview-05-06"] {"allow-input":true, isTemplate: true}
MODEL_ID:
gemini-2.5-flash-preview-05-20

Using local files
This simple example shows how can you use local files (presumed to load quickly) with the SDK's async API.


[ ]
prompt = "Describe this image in just 3 words."

img_filenames = ["firefighter.jpg", "elephants.jpeg", "jetpack.jpg"]
img_dir = "https://storage.googleapis.com/generativeai-downloads/images/"
Start by downloading the files locally.


[ ]
!wget -nv {img_dir}{{{','.join(img_filenames)}}}
2025-05-16 13:54:47 URL:https://storage.googleapis.com/generativeai-downloads/images/firefighter.jpg [547369/547369] -> "firefighter.jpg" [1]
2025-05-16 13:54:47 URL:https://storage.googleapis.com/generativeai-downloads/images/elephants.jpeg [224007/224007] -> "elephants.jpeg" [1]
2025-05-16 13:54:47 URL:https://storage.googleapis.com/generativeai-downloads/images/jetpack.jpg [357568/357568] -> "jetpack.jpg" [1]
FINISHED --2025-05-16 13:54:47--
Total wall clock time: 0.4s
Downloaded: 3 files, 1.1M in 0.01s (92.5 MB/s)
The async code uses the aio.models.generate_content method to invoke the API. Most async API methods can be found in the aio namespace.

Note that this code is not run in parallel. The async call indicates that the event loop can yield to other tasks, but there are no other tasks scheduled in this code. This may be sufficient, e.g. if you are running this in a web server request handler as it will allow the handler to yield to other tasks while waiting for the API response.


[ ]
import PIL

async def describe_local_images():

  for img_filename in img_filenames:

    img = PIL.Image.open(img_filename)
    r = await client.aio.models.generate_content(
        model=MODEL_ID,
        contents=[prompt, img]
    )
    print(r.text)


await describe_local_images()
Cat in tree.
Elephant family group
Jetpack Backpack Sketch
Downloading images asynchronously and in parallel
This example shows a more real-world case where an image is downloaded from an external source using the async HTTP library aiohttp, and each image is processed in parallel.


[ ]
import io, aiohttp, asyncio

async def download_image(session: aiohttp.ClientSession, img_url: str) -> PIL.Image:
  """Returns a PIL.Image object from the provided URL."""
  async with session.get(img_url) as img_resp:
    buffer = io.BytesIO()
    buffer.write(await img_resp.read())
    return PIL.Image.open(buffer)


async def process_image(img_future: asyncio.Future[PIL.Image]) -> str:
  """Summarise the image using the Gemini API."""
  # This code uses a future so that it defers work as late as possible. Using a
  # concrete Image object would require awaiting the download task before *queueing*
  # this content generation task - this approach chains the futures together
  # so that the download only starts when the generation is scheduled.
  r = await client.aio.models.generate_content(
      model=MODEL_ID,
      contents=[prompt, await img_future]
  )
  return r.text

[ ]
async def download_and_describe():

  async with aiohttp.ClientSession() as sesh:
    response_futures = []
    for img_filename in img_filenames:

      # Create the image download tasks (this does not schedule them yet).
      img_future = download_image(sesh, img_dir + img_filename)

      # Kick off the Gemini API request using the pending image download tasks.

Download and content generation queued for 3 images.

Jetpack backpack sketch

Cat up tree

Elephant trio nature
In the above example, a coroutine is created for each image that both downloads and then summarizes the image. The coroutines are executed in the final step, in the as_completed loop. To start them as early as possible without blocking the other work, you could wrap download_image in asyncio.ensure_future, but for this example the execution has been deferred to keep the creation and execution concerns separate.

Next Steps
Check out the AsyncClient class in the Python SDK reference.
Read more on Python's asyncio library
