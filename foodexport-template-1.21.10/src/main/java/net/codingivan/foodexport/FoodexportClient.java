package net.codingivan.foodexport;

import net.fabricmc.api.ClientModInitializer;
import net.fabricmc.fabric.api.client.event.lifecycle.v1.ClientTickEvents;
import net.minecraft.client.MinecraftClient;
import net.minecraft.client.gui.screen.Screen;
import net.minecraft.client.gui.screen.ingame.GenericContainerScreen;
import net.minecraft.item.ItemStack;
import net.minecraft.text.Text;

import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;

public class FoodexportClient implements ClientModInitializer {

    private boolean wasChestOpen = false;
    private GenericContainerScreen lastChestScreen = null;

    @Override
    public void onInitializeClient() {
        ClientTickEvents.END_CLIENT_TICK.register(client -> {
            if (client == null || client.player == null) return;

            Screen current = client.currentScreen;

            // Detect when a chest is open
            if (current instanceof GenericContainerScreen containerScreen) {
                wasChestOpen = true;
                lastChestScreen = containerScreen;
            }
            // Detect when chest closes (previous tick had chest, now null)
            else if (wasChestOpen && current == null) {
                if (lastChestScreen != null) {
                    exportChestContents(client, lastChestScreen);
                }
                wasChestOpen = false;
                lastChestScreen = null;
            }
        });
    }

    private void exportChestContents(MinecraftClient client, GenericContainerScreen chestScreen) {
        var handler = chestScreen.getScreenHandler();
        var slots = handler.slots;

        // The chest inventory is always the *first* part of slots before player inventory
        // For single chests: 27 slots (3x9)
        // For double chests: 54 slots (6x9)
        int containerSize = handler.getRows() * 9; // works for any chest size

        Path exportPath = client.runDirectory.toPath().resolve("chest_export.txt");

        StringBuilder builder = new StringBuilder();
        builder.append("Chest Export from player: ")
                .append(client.player.getName().getString())
                .append("\n\n");

        for (int i = 0; i < containerSize; i++) {
            ItemStack stack = slots.get(i).getStack();
            if (!stack.isEmpty()) {
                builder.append(stack.getCount())
                        .append(" x ")
                        .append(stack.getName().getString())
                        .append("\n");
            }
        }

        try {
            Files.writeString(exportPath, builder.toString(), StandardCharsets.UTF_8);
            client.player.sendMessage(Text.literal("✅ Chest exported to: " + exportPath.toAbsolutePath()), false);
        } catch (IOException e) {
            client.player.sendMessage(Text.literal("❌ Failed to export chest: " + e.getMessage()), false);
        }
    }
}
