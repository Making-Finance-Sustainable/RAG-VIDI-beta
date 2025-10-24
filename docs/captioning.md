## Captioning Benchmark

### Overview Norges Bank (XX pages)

| Parsing   | Captioning      | Accelerator | Tokens  | Seconds | 
|:----------|:----------------|:------------|:--------|:--------|
| Docling   |                 | CPU         | 26,161  | 317     |
| Docling   |                 | GPU         | 26,160  | 96      |
| Docling   | SmolVLM (256M)  | GPU         | 28,285  | 250     |
| Docling   | Granite Docling | GPU         | 27,576  | 641     |

### Captioning Examples

<img style="width: 95%; display: block; margin: auto;" src="https://making-finance-sustainable.github.io/RAG-VIDI-beta/images/Norges-Bank-01.jpg">

#### Docling Parsing and SmolVLM (256M)

> Government Pension Fund Global Annual report 2023
>
> In this image we can see a boy running on the road. In the background, we can see the snow, trees, houses, fencing, road, and the sky.
>
> In this image we can see a person holding a baby.

#### Granite Docling

> Government Pension Fund Global Annual report 2023
> 
> In this image I can see a child is standing on the road. On the left side there is a house. At the top there is snow.
> 
> In this image I can see a person hand and I can see a baby hand. Background is blurred.

#### Qwen 3 (2B)

> Government Pension Fund Global Annual report 2023
>
> A young child in a dark blue snowsuit and beanie is joyfully jumping over a puddle on a snow-covered street. The child's face is lit with a smile as they leap, capturing a moment of pure, unbridled happiness in a winter scene. The background features snow-laden houses and trees, creating a peaceful, wintry atmosphere.
>
> A close-up captures a baby's tiny hand gently held by an adult's larger hand, both wrapped in soft, textured fabric. The baby is nestled in a white knitted blanket, and the scene is softly lit, creating a warm and tender atmosphere. The image is framed with a dark blue diagonal overlay on the upper right.

<br />
[BACK TO THE HOME](https://making-finance-sustainable.github.io/RAG-VIDI-beta/)