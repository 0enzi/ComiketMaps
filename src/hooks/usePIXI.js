import { useState, useEffect, useRef, useCallback } from "react";
import * as PIXI from "pixi.js";
import { Viewport } from "pixi-viewport";

export const usePIXI = (activeImage, activeDay, markerData, onMarkerClick) => {
  const canvasRef = useRef(null);
  const pixiAppRef = useRef(null);
  const viewportRef = useRef(null);
  const spriteRef = useRef(null);
  const markersContainerRef = useRef(null);
  const initializedRef = useRef(false);
  const firstLoadRef = useRef(true);
  const resizeTimeoutRef = useRef(null);

  const previousStateRef = useRef({
    zoom: 1,
    centerX: 0,
    centerY: 0,
  });

  const [zoomLevel, setZoomLevel] = useState(1);
  const [windowSize, setWindowSize] = useState({
    width: window.innerWidth,
    height: window.innerHeight,
  });

  const isMobile = /iPhone|iPad|iPod|Android/i.test(navigator.userAgent);

  const createMarkers = useCallback(
    (imageIndex, day) => {
      console.log(`Creating markers for image ${imageIndex + 1}, ${day}`);

      if (!viewportRef.current || !spriteRef.current) {
        console.error(
          "Cannot create markers: viewport or sprite not available"
        );
        return;
      }

      if (markersContainerRef.current) {
        console.log("Clearing existing markers");
        if (
          viewportRef.current.children.includes(markersContainerRef.current)
        ) {
          viewportRef.current.removeChild(markersContainerRef.current);
        }
        markersContainerRef.current.destroy({ children: true });
        markersContainerRef.current = null;
      }

      const markers = markerData[day]?.[imageIndex] || [];
      console.log(
        `Found ${markers.length} markers for image ${imageIndex + 1}, ${day}`
      );

      if (markers.length === 0) {
        console.log("No markers to create");
        return;
      }

      const container = new PIXI.Container();
      markersContainerRef.current = container;

      const sprite = spriteRef.current;

      const spriteLeft = sprite.x - sprite.width / 2;
      const spriteTop = sprite.y - sprite.height / 2;

      markers.forEach((marker, index) => {
        const markerContainer = new PIXI.Container();

        markerContainer.x = spriteLeft + marker.x;
        markerContainer.y = spriteTop + marker.y;

        markerContainer.eventMode = "static";
        markerContainer.cursor = "pointer";

        const boxSize = 20;
        const box = new PIXI.Graphics();

        box.rect(-boxSize / 2, -boxSize / 2, boxSize, boxSize);
        box.fill(0x00ffff);
        box.stroke({
          width: 1,
          color: 0x000000,
          alpha: 1,
        });

        markerContainer.addChild(box);

        const boothNumber = marker.booth_no || (index + 1).toString();
        const numberText = new PIXI.Text({
          text: boothNumber,
          style: {
            fontFamily: "Arial",
            fontSize: 15,
            fill: 0x000000,
            fontWeight: "bold",
          },
        });
        numberText.anchor.set(0.5);
        markerContainer.addChild(numberText);

        markerContainer.on("pointerdown", (e) => {
          e.stopPropagation();
          onMarkerClick(marker);
        });

        container.addChild(markerContainer);
      });

      viewportRef.current.addChild(container);
      console.log("Markers created successfully");
    },
    [onMarkerClick, isMobile]
  );

  const loadImage = useCallback(
    async (imageIndex, day, preserveZoom = false) => {
      console.log(
        `loadImage called for image ${
          imageIndex + 1
        }, ${day}, preserveZoom: ${preserveZoom}`
      );

      if (!pixiAppRef.current || !viewportRef.current) {
        console.error("Cannot load image: PIXI not initialized");
        return false;
      }

      try {
        const app = pixiAppRef.current;
        const viewport = viewportRef.current;

        if (spriteRef.current && preserveZoom) {
          previousStateRef.current = {
            zoom: viewport.scale.x,
            centerX: viewport.center.x,
            centerY: viewport.center.y,
          };
          console.log("Saved previous state:", previousStateRef.current);
        }

        console.log("Cleaning up existing sprite and markers...");

        if (spriteRef.current) {
          console.log("Destroying existing sprite...");

          if (spriteRef.current.parent) {
            spriteRef.current.parent.removeChild(spriteRef.current);
          }

          spriteRef.current.destroy({
            children: true,
            texture: true,
            baseTexture: false,
          });

          spriteRef.current = null;
        }

        if (markersContainerRef.current) {
          console.log("Removing existing markers...");
          if (viewport.children.includes(markersContainerRef.current)) {
            viewport.removeChild(markersContainerRef.current);
          }
          markersContainerRef.current.destroy({ children: true });
          markersContainerRef.current = null;
        }

        const childrenToRemove = [];
        for (let i = viewport.children.length - 1; i >= 0; i--) {
          const child = viewport.children[i];

          if (
            child &&
            child !== spriteRef.current &&
            child !== markersContainerRef.current
          ) {
            if (child.texture || child.isSprite) {
              childrenToRemove.push(i);
            }
          }
        }

        childrenToRemove
          .sort((a, b) => b - a)
          .forEach((index) => {
            const child = viewport.getChildAt(index);
            if (child) {
              viewport.removeChildAt(index);
              if (child.destroy) {
                child.destroy({ children: true, texture: true });
              }
            }
          });

        if (childrenToRemove.length > 0) {
          console.log(`Removed ${childrenToRemove.length} stray objects`);
        }

        const imageUrls = {
        "Day 1": [
            "https://res.cloudinary.com/dx6o12mfe/image/upload/v1766902099/image1_t4hsjw.png",
            "https://res.cloudinary.com/dx6o12mfe/image/upload/v1766902099/image2_uqsi37.png",
            "https://res.cloudinary.com/dx6o12mfe/image/upload/v1766902099/image3_onc2fl.png",
            "https://res.cloudinary.com/dx6o12mfe/image/upload/v1766902100/image4_l2oysh.png"
        ],
        "Day 2": [
            "https://res.cloudinary.com/dx6o12mfe/image/upload/v1766902099/image1_t4hsjw.png",
            "https://res.cloudinary.com/dx6o12mfe/image/upload/v1766902099/image2_uqsi37.png",
            "https://res.cloudinary.com/dx6o12mfe/image/upload/v1766902099/image3_onc2fl.png",
            "https://res.cloudinary.com/dx6o12mfe/image/upload/v1766902100/image4_l2oysh.png"
        ]
        };
        const imageUrl = imageUrls[day]?.[imageIndex];

        console.log(`Loading image from: ${imageUrl}`);

        let texture;
        try {
          texture = await PIXI.Assets.load(imageUrl);
          console.log("✓ Image loaded successfully from URL");
        } catch (err) {
          console.log("✗ Image not found, creating placeholder");

          const canvas = document.createElement("canvas");
          canvas.width = 800;
          canvas.height = 600;
          const ctx = canvas.getContext("2d");

          const day1Colors = ["#1a237e", "#0d47a1", "#1565c0", "#1976d2"];
          const day2Colors = ["#004d40", "#00695c", "#00796b", "#00897b"];
          const colors = day === "Day 1" ? day1Colors : day2Colors;

          ctx.fillStyle = colors[imageIndex] || "#000000";
          ctx.fillRect(0, 0, 800, 600);

          ctx.fillStyle = "white";
          ctx.font = "bold 48px Arial";
          ctx.textAlign = "center";
          ctx.fillText(`Map ${imageIndex + 1}`, 400, 250);

          ctx.font = "bold 24px Arial";
          ctx.fillText(`${day}`, 400, 300);

          texture = PIXI.Texture.from(canvas);
        }

        const sprite = new PIXI.Sprite(texture);
        sprite.eventMode = "none";
        spriteRef.current = sprite;

        sprite.anchor.set(0.5);

        sprite.x = viewport.worldWidth / 2;
        sprite.y = viewport.worldHeight / 2;

        viewport.addChild(sprite);
        console.log("✓ New sprite added to viewport");

        console.log(
          `Viewport now has ${viewport.children.length} children after cleanup`
        );

        let targetZoom, targetCenterX, targetCenterY;

        if (preserveZoom && previousStateRef.current.zoom > 0) {
          targetZoom = previousStateRef.current.zoom;
          targetCenterX = previousStateRef.current.centerX;
          targetCenterY = previousStateRef.current.centerY;
          console.log("Using saved zoom:", targetZoom);
        } else {
          const viewportWidth = viewport.screenWidth;
          const viewportHeight = viewport.screenHeight;

          const scaleX = viewportWidth / sprite.width;
          const scaleY = viewportHeight / sprite.height;

          targetZoom = Math.min(scaleX, scaleY) * 0.9;
          targetCenterX = sprite.x;
          targetCenterY = sprite.y;
          console.log("Calculating new zoom:", targetZoom);
        }

        viewport.setZoom(targetZoom, true);
        viewport.moveCenter(targetCenterX, targetCenterY);
        setZoomLevel(targetZoom);

        console.log(`✓ Zoom set to: ${targetZoom.toFixed(2)}x`);

        createMarkers(imageIndex, day);

        if (firstLoadRef.current) {
          firstLoadRef.current = false;
        }

        return true;
      } catch (error) {
        console.error("✗ Error loading image:", error);
        return false;
      }
    },
    [createMarkers, isMobile]
  );

  const initializePixi = useCallback(async () => {
    console.log("initializePixi called");

    if (!canvasRef.current || initializedRef.current) {
      console.log("Skipping PIXI initialization");
      return;
    }

    try {
      console.log(
        `Initializing PIXI with window size: ${windowSize.width}x${windowSize.height} (mobile: ${isMobile})`
      );

      const app = new PIXI.Application();

      await app.init({
        canvas: canvasRef.current,
        width: Math.max(1, windowSize.width),
        height: Math.max(1, windowSize.height),
        backgroundColor: 0x0a0a0a,
        resolution: window.devicePixelRatio || 1,
        antialias: true,
        autoDensity: true,
      });

      pixiAppRef.current = app;
      console.log("✓ PIXI Application created");

      const viewport = new Viewport({
        screenWidth: windowSize.width,
        screenHeight: windowSize.height,
        worldWidth: windowSize.width * 2,
        worldHeight: windowSize.height * 2,
        ticker: app.ticker,
        events: app.renderer.events,
        passiveWheel: false,
        stopPropagation: true,
      });

      app.stage.addChild(viewport);
      viewportRef.current = viewport;
      console.log("✓ Viewport created and added to stage");

      viewport
        .drag({
          pressDrag: false,
          wheel: false,
          factor: 1,
        })
        .pinch({
          factor: 1,
        })
        .wheel({
          smooth: 10,
          interrupt: true,
        })
        .decelerate();

      viewport.clampZoom({
        minScale: 0.1,
        maxScale: 10,
      });

      viewport.moveCenter(viewport.worldWidth / 2, viewport.worldHeight / 2);

      viewport.on("zoomed", () => {
        setZoomLevel(viewport.scale.x);
      });

      viewport.on("clicked", (e) => {
        const worldPos = e.world;
        if (spriteRef.current) {
          const sprite = spriteRef.current;
          const spriteLeft = sprite.x - sprite.width / 2;
          const spriteTop = sprite.y - sprite.height / 2;
          const imageX = worldPos.x - spriteLeft;
          const imageY = worldPos.y - spriteTop;
          const roundedX = Math.round(imageX);
          const roundedY = Math.round(imageY);

          console.log("══════════════════════════════════════════════════");
          console.log("🎯 CLICK COORDINATES (TOP-LEFT RELATIVE):");
          console.log(`x: ${roundedX}, y: ${roundedY}`);
          console.log("");
          console.log("📋 Copy this for markerData.js:");
          console.log(`x: ${roundedX},`);
          console.log(`y: ${roundedY},`);
          console.log("══════════════════════════════════════════════════");

          navigator.clipboard
            .writeText(`${roundedX}, ${roundedY}`)
            .then(() => console.log("✅ Coordinates copied to clipboard!"))
            .catch((err) => console.error("Failed to copy:", err));
        }
      });

      initializedRef.current = true;
      console.log("✓ PIXI initialization complete");
      console.log("🎯 Coordinate debug enabled!");
      console.log("👉 Click to get formatted coordinates for markerData.js");

      await loadImage(activeImage, activeDay, false);
    } catch (error) {
      console.error("✗ Failed to initialize PIXI:", error);
    }
  }, [activeImage, activeDay, loadImage, windowSize, isMobile]);

  useEffect(() => {
    const updateWindowSize = () => {
      setWindowSize({
        width: window.innerWidth,
        height: window.innerHeight,
      });
    };

    updateWindowSize();
    window.addEventListener("resize", updateWindowSize);

    return () => {
      window.removeEventListener("resize", updateWindowSize);
      if (resizeTimeoutRef.current) {
        clearTimeout(resizeTimeoutRef.current);
      }
    };
  }, []);

  useEffect(() => {
    if (!initializedRef.current) {
      console.log("Starting PIXI initialization...");
      initializePixi();
    }

    const handleResize = () => {
      if (resizeTimeoutRef.current) {
        clearTimeout(resizeTimeoutRef.current);
      }

      resizeTimeoutRef.current = setTimeout(() => {
        if (!pixiAppRef.current || !viewportRef.current) {
          return;
        }

        const app = pixiAppRef.current;
        const viewport = viewportRef.current;

        if (windowSize.width <= 0 || windowSize.height <= 0) {
          return;
        }

        try {
          if (
            app.renderer.width !== windowSize.width ||
            app.renderer.height !== windowSize.height
          ) {
            app.renderer.resize(windowSize.width, windowSize.height);
            viewport.resize(
              windowSize.width,
              windowSize.height,
              windowSize.width * 2,
              windowSize.height * 2
            );

            if (spriteRef.current) {
              const sprite = spriteRef.current;
              const viewportWidth = viewport.screenWidth;
              const viewportHeight = viewport.screenHeight;

              const scaleX = viewportWidth / sprite.width;
              const scaleY = viewportHeight / sprite.height;
              const newScale = Math.min(scaleX, scaleY) * 0.9;

              viewport.setZoom(newScale, true);
              viewport.moveCenter(sprite.x, sprite.y);
              setZoomLevel(newScale);
            }
          }
        } catch (error) {
          console.error("Error during resize:", error);
        }
      }, 100);
    };

    handleResize();

    return () => {
      if (resizeTimeoutRef.current) {
        clearTimeout(resizeTimeoutRef.current);
      }
    };
  }, [initializePixi, windowSize, isMobile]);

  useEffect(() => {
    if (firstLoadRef.current) {
      return;
    }

    if (pixiAppRef.current && viewportRef.current && initializedRef.current) {
      console.log(`Loading image ${activeImage + 1} for ${activeDay}...`);
      loadImage(activeImage, activeDay, true);
    }
  }, [activeImage, activeDay, loadImage]);

  useEffect(() => {
    return () => {
      if (pixiAppRef.current) {
        console.log("Destroying PIXI application");
        try {
          pixiAppRef.current.destroy(true);
          pixiAppRef.current = null;
          viewportRef.current = null;
          spriteRef.current = null;
          markersContainerRef.current = null;
          initializedRef.current = false;
          firstLoadRef.current = true;
        } catch (err) {
          console.error("✗ Error during PIXI cleanup:", err);
        }
      }
    };
  }, []);

  const handleZoomIn = () => {
    if (viewportRef.current) {
      const newScale = Math.min(10, zoomLevel * 1.2);
      viewportRef.current.setZoom(newScale, true);
      setZoomLevel(newScale);
    }
  };

  const handleZoomOut = () => {
    if (viewportRef.current) {
      const newScale = Math.max(0.1, zoomLevel * 0.8);
      viewportRef.current.setZoom(newScale, true);
      setZoomLevel(newScale);
    }
  };

  const handleResetZoom = () => {
    if (viewportRef.current && spriteRef.current) {
      const viewport = viewportRef.current;
      const sprite = spriteRef.current;

      const scaleX = viewport.screenWidth / sprite.width;
      const scaleY = viewport.screenHeight / sprite.height;
      const initialScale = Math.min(scaleX, scaleY) * 0.9;

      viewport.setZoom(initialScale, true);
      viewport.moveCenter(sprite.x, sprite.y);
      setZoomLevel(initialScale);
    }
  };

  return {
    canvasRef,
    zoomLevel,
    handleZoomIn,
    handleZoomOut,
    handleResetZoom,
    isMobile,
  };
};
