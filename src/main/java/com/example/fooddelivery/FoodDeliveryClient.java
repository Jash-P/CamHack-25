package com.example.fooddelivery;

import net.fabricmc.api.ClientModInitializer;
import net.fabricmc.fabric.api.client.event.lifecycle.v1.ClientTickEvents;
import net.fabricmc.fabric.api.client.keybinding.v1.KeyBindingHelper;
import net.minecraft.client.MinecraftClient;
import net.minecraft.client.option.KeyBinding;
import net.minecraft.client.util.InputUtil;
import net.minecraft.inventory.Inventory;
import net.minecraft.screen.GenericContainerScreenHandler;
import net.minecraft.screen.ScreenHandler;
import net.minecraft.text.Text;
import org.lwjgl.glfw.GLFW;

import java.io.File;
import java.io.IOException;
import java.io.PrintWriter;
import java.time.LocalDateTime;
import java.time.format.DateTimeFormatter;

public class FoodDeliveryClient implements ClientModInitializer {

    private static KeyBinding exportKey;

    @Override
    public void onInitializeClient() {
        // Register a keybinding (default: O key)
        exportKey = KeyBindingHelper.registerKeyBinding(new KeyBinding(
                "key.fooddelivery.export",
                InputUtil.Type.KEYSYM,
                GLFW.GLFW_KEY_O,
                KeyBinding.MISC_CATEGORY
        ));

        // Register tick event to check key presses
        ClientTickEvents.END_CLIENT_TICK.register(client -> {
            while (exportKey.wasPressed()) {
                exportChestContents(client);
            }
        });
    }

    private void exportChestContents(MinecraftClient client) {
        // Make sure the player has a screen open
        if (client.player == null || client.player.currentScreenHandler == null) {
            client.player.sendMessage(Text.literal("No chest open!"), false);
            return;
        }

        ScreenHandler handler = client.player.currentScreenHandler;

        // Only export if the screen is a chest/container
        if (!(handler instanceof GenericContainerScreenHandler)) {
            client.player.sendMessage(Text.literal("Not a container!"), false);
            return;
        }

        GenericContainerScreenHandler chestHandler = (GenericContainerScreenHandler) handler;
        for (int i = 0; i < chestHandler.slots.size(); i++) {
            var stack = chestHandler.slots.get(i).getStack();
            if (!stack.isEmpty()) {
                writer.println(stack.getName().getString() + " x" + stack.getCount());
            }
        }

        try {
            // Create output folder
            File exportDir = new File(client.runDirectory, "chest_exports");
            if (!exportDir.exists()) exportDir.mkdirs();

            // File name with timestamp
            String timestamp = LocalDateTime.now().format(DateTimeFormatter.ofPattern("yyyy-MM-dd_HH-mm-ss"));
            File file = new File(exportDir, "chest_" + timestamp + ".txt");

            try (PrintWriter writer = new PrintWriter(file)) {
                for (int i = 0; i < inventory.size(); i++) {
                    if (!inventory.getStack(i).isEmpty()) {
                        writer.println(inventory.getStack(i).getName().getString() + " x" + inventory.getStack(i).getCount());
                    }
                }
            }

            client.player.sendMessage(Text.literal("Chest exported to: " + file.getAbsolutePath()), false);
        } catch (IOException e) {
            e.printStackTrace();
            client.player.sendMessage(Text.literal("Failed to export chest!"), false);
        }
    }
}
