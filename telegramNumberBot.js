const express = require("express");
const app = express();
const PORT = process.env.PORT || 3000;

// Keep-alive route
app.get("/", (req, res) => {
  res.send("Server is alive!");
});

// Start Express server
app.listen(PORT, () => {
  console.log(`Express server running on port ${PORT}`);
});

const { Telegraf, session } = require("telegraf");
const fs = require("fs-extra");
const path = require("path");
const puppeteer = require("puppeteer");

const bot = new Telegraf("8566731317:AAHlkUDl3Z6hYuh2vPUXSgoULD9CGVRUUkw");
const ADMIN_PASSWORD = "ABab@3574";
const NUMBERS_FILE = path.join(__dirname, "numbers.txt");
const COUNTRIES_FILE = path.join(__dirname, "countries.json");
const CHANNEL_ID = "@fxsentarofotp";
const USERS_FILE = path.join(__dirname, "users.json");
const OUTPUT_FILE = path.join(__dirname, "sms_cdr_stats.txt");
const { Markup } = require("telegraf");

// Define the custom command menu with a "Start" button`
bot.telegram.setMyCommands([
  { command: "start", description: "Start the bot" },
]);

// Example main menu
const mainMenu = Markup.keyboard([
  ["📞 Get Number", "HELP ?"],
  ["🏠 Start Menu", "🔗 Join Channel"],
]).resize();

const default_countries = {
  221: { name: "Senegal", flag: "🇸🇳" },
  225: { name: "Côte d'Ivoire", flag: "🇨🇮" },
  996: { name: "Kyrgyzstan", flag: "🇰🇬" },
  95: { name: "Myanmar", flag: "🇲🇲" },
  251: { name: "Ethiopia", flag: "🇪🇹" },
};

bot.use(session());

// Ensure session is always initialized with better error handling
bot.use(async (ctx, next) => {
  try {
    ctx.session = ctx.session || {};
    ctx.session.isVerified = ctx.session.isVerified || false;
    ctx.session.currentNumber = ctx.session.currentNumber || null;
    ctx.session.lastOtpMessageId = ctx.session.lastOtpMessageId || null;
    ctx.session.otpPollingInterval = ctx.session.otpPollingInterval || null;
    ctx.session.isAdmin = ctx.session.isAdmin || false;
    ctx.session.waitingForForceUpload =
      ctx.session.waitingForForceUpload || false;
    ctx.session.processedOtps = ctx.session.processedOtps || {};
    ctx.session.otpTimeoutReached = ctx.session.otpTimeoutReached || false;
    ctx.session.otpMessageIds = ctx.session.otpMessageIds || [];

    // Clean up any orphaned polling intervals
    if (
      ctx.session.otpPollingInterval &&
      typeof ctx.session.otpPollingInterval === "number"
    ) {
      try {
        clearInterval(ctx.session.otpPollingInterval);
      } catch (error) {
        console.error("Error clearing interval:", error);
      }
      ctx.session.otpPollingInterval = null;
    }

    return next();
  } catch (error) {
    console.error("Error in session middleware:", error);
    return next();
  }
});

let countries = default_countries;
if (fs.pathExistsSync(COUNTRIES_FILE)) {
  try {
    countries = JSON.parse(fs.readFileSync(COUNTRIES_FILE, "utf8"));
    console.log("Loaded countries:", JSON.stringify(countries, null, 2));
  } catch (error) {
    console.error("Error loading countries.json:", error);
    fs.writeFileSync(COUNTRIES_FILE, JSON.stringify(default_countries));
    countries = default_countries;
  }
} else {
  fs.writeFileSync(COUNTRIES_FILE, JSON.stringify(countries));
  console.log("Created countries.json with default countries");
}

function saveCountries() {
  try {
    fs.writeFileSync(COUNTRIES_FILE, JSON.stringify(countries));
    console.log("Saved countries to countries.json");
  } catch (error) {
    console.error("Error saving countries.json:", error);
  }
}

// Helper function to extract country code from phone number
function getCountryCode(number) {
  // Try 3 digits first, then 2 digits
  const threeDigit = number.slice(0, 3);
  if (countries[threeDigit]) {
    console.log(`Matched country code ${threeDigit} for number ${number}`);
    return threeDigit;
  }

  const twoDigit = number.slice(0, 2);
  if (countries[twoDigit]) {
    console.log(`Matched country code ${twoDigit} for number ${number}`);
    return twoDigit;
  }

  console.log(`No country code matched for number ${number}`);
  return null;
}

let numbersByCountry = {};
if (fs.pathExistsSync(NUMBERS_FILE)) {
  try {
    const rawContent = fs.readFileSync(NUMBERS_FILE, "utf8");
    console.log("Raw content of numbers.txt:", rawContent);
    const lines = rawContent
      .split(/\r?\n/)
      .filter((line) => line.trim() !== "");
    console.log(`Found ${lines.length} lines in numbers.txt`);

    const invalidNumbers = [];
    lines.forEach((number, index) => {
      number = number.trim();
      console.log(`Processing line ${index + 1}: ${number}`);
      if (/^\d{10,15}$/.test(number)) {
        const countryCode = getCountryCode(number);
        if (countryCode) {
          if (!numbersByCountry[countryCode]) {
            numbersByCountry[countryCode] = [];
          }
          if (!numbersByCountry[countryCode].includes(number)) {
            numbersByCountry[countryCode].push(number);
            console.log(`Added number ${number} to country ${countryCode}`);
          } else {
            console.log(
              `Skipped duplicate number ${number} for country ${countryCode}`
            );
          }
        } else {
          invalidNumbers.push(number);
          console.log(`Number ${number} skipped: no matching country code`);
        }
      } else {
        invalidNumbers.push(number);
        console.log(
          `Number ${number} skipped: invalid format (must be 10-15 digits)`
        );
      }
    });

    if (invalidNumbers.length > 0) {
      console.log(`Invalid or unmatched numbers: ${invalidNumbers.join(", ")}`);
    }
    console.log(
      "Final numbersByCountry:",
      JSON.stringify(numbersByCountry, null, 2)
    );
  } catch (error) {
    console.error("Error loading numbers.txt:", error);
  }
} else {
  console.log("No numbers.txt file found.");
}

function saveNumbers() {
  try {
    const lines = Object.values(numbersByCountry).flat();
    console.log(`Saving ${lines.length} numbers to numbers.txt`);
    fs.writeFileSync(NUMBERS_FILE, lines.join("\n"));
  } catch (error) {
    console.error("Error saving numbers.txt:", error);
  }
}

function getNumberForCountry(countryCode) {
  if (
    !numbersByCountry[countryCode] ||
    numbersByCountry[countryCode].length === 0
  ) {
    console.log(`No numbers available for country ${countryCode}`);
    return null;
  }

  // Filter out already assigned numbers
  const availableNumbers = numbersByCountry[countryCode].filter(
    (number) => !assignedNumbers[number]
  );

  if (availableNumbers.length === 0) {
    console.log(`No unassigned numbers available for country ${countryCode}`);
    return null;
  }

  const index = Math.floor(Math.random() * availableNumbers.length);
  console.log(
    `Selected number ${availableNumbers[index]} for country ${countryCode}`
  );
  return availableNumbers[index];
}

function removeNumberFromCountry(countryCode, number) {
  if (numbersByCountry[countryCode]) {
    const index = numbersByCountry[countryCode].indexOf(number);
    if (index !== -1) {
      numbersByCountry[countryCode].splice(index, 1);
      console.log(`Removed number ${number} from country ${countryCode}`);
    }
    if (numbersByCountry[countryCode].length === 0) {
      delete numbersByCountry[countryCode];
      console.log(`Removed empty country ${countryCode} from numbersByCountry`);
    }
  }
}

// Load or initialize users
let users = {};
let assignedNumbers = {}; // Track which numbers are currently assigned to which users
if (fs.pathExistsSync(USERS_FILE)) {
  try {
    users = JSON.parse(fs.readFileSync(USERS_FILE, "utf8"));
    console.log("Loaded users:", JSON.stringify(users, null, 2));
  } catch (error) {
    console.error("Error loading users.json:", error);
  }
} else {
  fs.writeFileSync(USERS_FILE, JSON.stringify(users));
  console.log("Created users.json");
}

function saveUsers() {
  try {
    fs.writeFileSync(USERS_FILE, JSON.stringify(users));
    console.log("Saved users to users.json");
  } catch (error) {
    console.error("Error saving users.json:", error);
  }
}

function addUser(chatId) {
  if (!users[chatId]) {
    users[chatId] = { joined: new Date().toISOString() };
    saveUsers();
  }
}

// Track assigned numbers to prevent conflicts
function assignNumberToUser(chatId, number) {
  // For number, remove any existing assignments for this user
  for (const [existingNumber, existingChatId] of Object.entries(
    assignedNumbers
  )) {
    if (existingChatId === chatId) {
      delete assignedNumbers[existingNumber];
      console.log(
        `Released existing number ${existingNumber} from user ${chatId}`
      );
    }
  }
  // Assign new number
  assignedNumbers[number] = chatId;
  console.log(`Assigned number ${number} to user ${chatId}`);
}

function releaseNumberFromUser(chatId, number) {
  if (assignedNumbers[number] === chatId) {
    delete assignedNumbers[number];
    console.log(`Released number ${number} from user ${chatId}`);
  }
}

function getAssignedNumberForUser(chatId) {
  for (const [number, assignedChatId] of Object.entries(assignedNumbers)) {
    if (assignedChatId === chatId) {
      return number;
    }
  }
  return null;
}

// Helper function to check and send OTP for a given number
async function checkForOtp(ctx, number, silent = false) {
  try {
    const existingData = await fs.readFile(OUTPUT_FILE, "utf8");
    const lines = existingData.split("\n").filter((line) => line.trim() !== "");

    // Find all lines where the Number field matches the user's selected number
    const matchingMessages = lines.filter((line) => {
      if (line.startsWith("OTP Code:")) {
        const parts = line.split(" Number: ");
        if (parts.length < 2) return false;
        const numberPart = parts[1].split(" Country: ")[0].trim();
        return numberPart === number;
      }
      return false;
    });

    if (matchingMessages.length > 0) {
      console.log(
        `Found ${matchingMessages.length} matching messages for number ${number}`
      );

      const processedOtps = ctx.session.processedOtps || {};

      let newOtpsFound = false;

      // ✅ Updated regex — Unicode-safe and spacing-tolerant
      const regex =
        /^OTP Code:\s*(\S+)\s+Number:\s*(\S+)\s+Country:\s*([\p{L}\p{M}\p{N}\p{Emoji_Presentation}\s]+?)\s+Service:\s*(\S+)\s+Message:\s*([\s\S]+?)\s+Date:\s*(.+)$/u;

      // Process all matching messages to find new OTPs
      for (const messageLine of matchingMessages) {
        const cleanLine = messageLine.trim().replace(/\s+/g, " "); // Normalize extra spaces
        const match = cleanLine.match(regex);

        if (!match) {
          console.log(`Invalid line format: ${messageLine}`);
          continue;
        }

        const [, otp, phoneNumber, country, service, message] = match;

        // Create a unique key for this OTP (otp + number + service)
        const otpKey = `${otp}_${phoneNumber}_${service}`;

        // Skip if we've already processed this OTP
        if (processedOtps[otpKey]) continue;

        console.log(
          `Found OTP: ${otp} for number ${phoneNumber}, service: ${service}`
        );

        // Mark this OTP as processed
        processedOtps[otpKey] = true;
        ctx.session.processedOtps = processedOtps;

        // Get country info (fallback to default globe icon)
        const countryCode = getCountryCode(phoneNumber);
        const countryInfo = countries[countryCode] || {
          name: country,
          flag: "🌍",
        };

        // Format the OTP message
        const formattedMessage = `📞 Number: \`${phoneNumber}\`\n🌐 Country: ${countryInfo.flag} ${countryInfo.name}\n🔧 Service: ${service}\n\n🔑 OTP Code: \`${otp}\`\n\n📜 Message: *${message}*\n\n\`${otp}\``;

        console.log(`Sending OTP message for number ${phoneNumber}: ${otp}`);

        // Send OTP to user
        const sentMessage = await ctx.reply(formattedMessage, {
          parse_mode: "Markdown",
          disable_notification: false,
        });

        // Store message IDs
        ctx.session.lastOtpMessageId = sentMessage.message_id;
        ctx.session.otpMessageIds = ctx.session.otpMessageIds || [];
        ctx.session.otpMessageIds.push(sentMessage.message_id);

        newOtpsFound = true;
      }

      return newOtpsFound;
    } else {
      // If no OTP is found
      if (!silent) {
        ctx.session.lastOtpMessageId = null;
      }
      return false;
    }
  } catch (error) {
    console.error("Error reading sms_cdr_stats.txt:", error);

    if (!silent) {
      ctx.session.lastOtpMessageId = null;

      await ctx.reply(
        '❌ Error fetching OTP. Please try again using "🔐 OTP Group".',
        {
          disable_notification: false,
        }
      );
    }
    return false;
  }
}

// Start OTP polling for a number with better error handling
function startOtpPolling(ctx, number) {
  try {
    const intervalKey = "otpPollingInterval";
    const timeoutKey = "otpTimeoutReached";

    if (ctx.session[intervalKey]) {
      clearInterval(ctx.session[intervalKey]);
    }

    // Reset timeout flag
    ctx.session[timeoutKey] = false;

    let pollCount = 0;
    const maxPolls = 120; // Maximum 50 seconds (25 * 2 seconds)

    ctx.session[intervalKey] = setInterval(async () => {
      try {
        pollCount++;

        // Stop polling after maximum attempts
        if (pollCount >= maxPolls) {
          clearInterval(ctx.session[intervalKey]);
          ctx.session[intervalKey] = null;
          ctx.session[timeoutKey] = true;

          // Send simple timeout message with buttons and sound
          const timeoutMessage = `❌ No OTP found for \`${number}\``;

          // Get the country code for the current number to create change number callback
          const countryCode = getCountryCode(number);

          await ctx.reply(timeoutMessage, {
            parse_mode: "Markdown",
            reply_markup: {
              inline_keyboard: [
                [
                  {
                    text: "🔄 Check Again",
                    callback_data: `check_otp_again:${number}:1`,
                  },
                ],
                [
                  {
                    text: "🔗 Check in OTP Group",
                    url: "https://t.me/otpkingfx",
                  },
                ],
              ],
            },
            disable_notification: false,
          });
          return;
        }

        const found = await checkForOtp(ctx, number, true); // Silent check
        if (found) {
          clearInterval(ctx.session[intervalKey]);
          ctx.session[intervalKey] = null;
        }
      } catch (error) {
        console.error("Error in OTP polling:", error);
        clearInterval(ctx.session[intervalKey]);
        ctx.session[intervalKey] = null;
      }
    }, 1000);
  } catch (error) {
    console.error("Error starting OTP polling:", error);
  }
}

bot.start(async (ctx) => {
  try {
    addUser(ctx.chat.id); // Add user to the list
    if (ctx.session.isVerified) {
      await ctx.reply(
        "✅ Verified! Welcome to 👑Fx King Number Bot! ✨",
        mainMenu
      );
    } else {
      await ctx.sendMessage("⚠️ First join the channel and verify.", {
        reply_markup: {
          inline_keyboard: [
            [{ text: "🔗 Join Channel", url: "https://t.me/fxsentarofotp" }],
            [{ text: "✅ Verify Channel", callback_data: "verify_channel" }],
          ],
        },
        disable_notification: false,
      });
    }
  } catch (error) {
    console.error("Error in start handler:", error);
    await ctx.reply("❌ An error occurred. Please try again.", {
      disable_notification: false,
    });
  }
});

bot.hears("📞 Get Number", async (ctx) => {
  try {
    const keyboard = Object.keys(countries).map((code, index) => {
      const totalNumbers = numbersByCountry[code]
        ? numbersByCountry[code].length
        : 0;
      const availableNumbers = numbersByCountry[code]
        ? numbersByCountry[code].filter((number) => !assignedNumbers[number])
            .length
        : 0;

      let statusText = "";
      if (availableNumbers === 0) {
        statusText = totalNumbers > 0 ? " 🔴 Used" : " 🔴 Used";
      } else {
        statusText = ` 🟢  ${availableNumbers}`;
      }

      return [
        {
          text: `${countries[code].flag} ${index + 1}. ${
            countries[code].name
          }${statusText}`,
          callback_data: `select:${code}`,
        },
      ];
    });

    await ctx.reply("📞 Get Number\n🌍 Select Your Country:", {
      reply_markup: { inline_keyboard: keyboard },
      disable_notification: false,
    });
  } catch (error) {
    console.error("Error in Get Number handler:", error);
    await ctx.reply(
      "❌ An error occurred while getting numbers. Please try again.",
      { disable_notification: false }
    );
  }
});

bot.action("verify_channel", async (ctx) => {
  try {
    // Answer callback query promptly to avoid timeout
    await ctx.answerCbQuery("⏳ Checking your channel membership...");

    const chatMember = await ctx.telegram.getChatMember(
      CHANNEL_ID,
      ctx.from.id
    );
    if (["member", "administrator", "creator"].includes(chatMember.status)) {
      ctx.session.isVerified = true;
      await ctx.editMessageText(
        "✅ Verification successful! You can now use the bot.",
        {
          reply_markup: {
            inline_keyboard: [
              [{ text: "📞 Get Number", callback_data: "getnumber" }],
            ],
          },
          disable_notification: false,
        }
      );
      await ctx.reply("📋 Main Menu:", mainMenu);
    } else {
      await ctx.reply(
        "⚠️ Please join the channel first: https://t.me/fxsentarofotp",
        { disable_notification: false }
      );
    }
  } catch (error) {
    console.error("Error in verify_channel action:", error);
    if (
      error.description?.includes("query is too old") ||
      error.description?.includes("query ID is invalid")
    ) {
      // Notify user to try again
      await ctx.reply(
        '⚠️ The verification request timed out. Please try again by clicking "Verify Channel".',
        {
          reply_markup: {
            inline_keyboard: [
              [{ text: "🔗 Join Channel", url: "https://t.me/fxsentarofotp" }],
              [{ text: "✅ Verify Channel", callback_data: "verify_channel" }],
            ],
          },
          disable_notification: false,
        }
      );
    } else {
      await ctx.reply(
        "❌ Error verifying membership. Ensure the bot is admin in the channel.",
        { disable_notification: false }
      );
    }
  }
});

bot.hears("🏠 Start Menu", async (ctx) => {
  try {
    await ctx.reply(
      "🏠 Welcome to 👑Fx King Number Bot! ✨\n\nChoose an option:",
      mainMenu
    );
  } catch (error) {
    console.error("Error in Start Menu handler:", error);
    await ctx.reply("❌ An error occurred. Please try again.", {
      disable_notification: false,
    });
  }
});

bot.hears("🔗 Join Channel", async (ctx) => {
  try {
    await ctx.reply("🔗 Please join our channel: https://t.me/fxsentarofotp", {
      disable_notification: false,
    });
  } catch (error) {
    console.error("Error in Join Channel handler:", error);
    await ctx.reply("❌ An error occurred. Please try again.", {
      disable_notification: false,
    });
  }
});

bot.hears("HELP ?", async (ctx) => {
  try {
    await ctx.reply("🔗 Talk to Admin", {
      reply_markup: {
        inline_keyboard: [
          [{ text: "🔗 Admin Support", url: "https://t.me/Imran25801235" }],
        ],
      },
      disable_notification: false,
    });
  } catch (error) {
    console.error("Error in OTP Group handler:", error);
    await ctx.reply("❌ An error occurred. Please try again.", {
      disable_notification: false,
    });
  }
});

bot.on("callback_query", async (ctx) => {
  try {
    const data = ctx.callbackQuery.data;

    // Input validation
    if (!data || typeof data !== "string") {
      return ctx.answerCbQuery("Invalid callback data");
    }

    if (data === "verify_channel") {
      // Handle verify_channel in its own action handler
      return; // Already handled by bot.action('verify_channel', ...)
    }

    addUser(ctx.chat.id);
    if (!ctx.session.isVerified) {
      await ctx.sendMessage("⚠️ First join the channel and verify.", {
        reply_markup: {
          inline_keyboard: [
            [{ text: "🔗 Join Channel", url: "https://t.me/fxsentarofotp" }],
            [{ text: "✅ Verify Channel", callback_data: "verify_channel" }],
          ],
        },
        disable_notification: false,
      });
      return ctx.answerCbQuery("Please verify channel membership first!", {
        show_alert: true,
      });
    }

    if (data === "getnumber") {
      const keyboard = Object.keys(countries).map((code, index) => {
        const totalNumbers = numbersByCountry[code]
          ? numbersByCountry[code].length
          : 0;
        const availableNumbers = numbersByCountry[code]
          ? numbersByCountry[code].filter((number) => !assignedNumbers[number])
              .length
          : 0;

        let statusText = "";
        if (availableNumbers === 0) {
          statusText = totalNumbers > 0 ? " 🔴 Used" : " 🔴 Used";
        } else {
          statusText = `  🟢 ${availableNumbers} `;
        }

        return [
          {
            text: `${countries[code].flag} ${index + 1}. ${
              countries[code].name
            }${statusText}`,
            callback_data: `select:${code}`,
          },
        ];
      });
      await ctx.editMessageText("📞 Get Number\n🌍 Select Your Country:", {
        reply_markup: { inline_keyboard: keyboard },
        disable_notification: false,
      });
      return ctx.answerCbQuery();
    }

    const parts = data.split(":");
    if (parts.length < 2) {
      return ctx.answerCbQuery("Invalid callback format");
    }

    const [action, countryCode, oldNumber] = parts;

    if (action === "check_otp_again") {
      const [actionName, number, numberType] = data.split(":");

      await ctx.answerCbQuery("🔄 Checking OTP again...");

      // Delete the timeout message that triggered this callback
      try {
        await ctx.deleteMessage();
      } catch (error) {
        console.error("Failed to delete timeout message:", error);
      }

      // Clear any existing polling
      if (ctx.session.otpPollingInterval) {
        clearInterval(ctx.session.otpPollingInterval);
        ctx.session.otpPollingInterval = null;
      }

      // Reset timeout flags
      ctx.session.otpTimeoutReached = false;

      // Start new polling for the number
      startOtpPolling(ctx, number);

      await ctx.reply(`🔄 Checking OTP again for \`${number}\`...`, {
        parse_mode: "Markdown",
        disable_notification: false,
      });
      return;
    }

    if (action === "used") {
      await ctx.answerCbQuery("Processing numbers as used...");

      // Parse the old numbers from the callback data
      const [actionName, countryCodeParam, oldNumber1] = data.split(":");

      // Delete all previous OTP messages
      if (ctx.session.otpMessageIds && ctx.session.otpMessageIds.length > 0) {
        for (const messageId of ctx.session.otpMessageIds) {
          try {
            await ctx.telegram.deleteMessage(ctx.chat.id, messageId);
            console.log(
              `Deleted OTP message ID ${messageId} for chat ${ctx.chat.id}`
            );
          } catch (error) {
            console.error(`Failed to delete message ID ${messageId}:`, error);
          }
        }
      }

      // Delete the message containing the "I Have Used" button
      try {
        await ctx.deleteMessage();
        console.log(
          `Deleted message with "I Have Used" button for chat ${ctx.chat.id}`
        );
      } catch (error) {
        console.error('Failed to delete "I Have Used" message:', error);
      }

      // Stop any existing polling
      if (ctx.session.otpPollingInterval) {
        clearInterval(ctx.session.otpPollingInterval);
        ctx.session.otpPollingInterval = null;
      }

      // Release and delete the used numbers completely to prevent history
      if (oldNumber1) {
        releaseNumberFromUser(ctx.chat.id, oldNumber1);
        removeNumberFromCountry(countryCodeParam, oldNumber1);
      }

      // Clear session data for old numbers
      ctx.session.currentNumber = null;
      ctx.session.lastOtpMessageId = null;
      ctx.session.otpMessageIds = [];
      ctx.session.processedOtps = {};

      // Get new numbers for the same country
      const newNumber = getNumberForCountry(countryCodeParam);

      if (!newNumber) {
        await ctx.reply(
          `✅ Previous numbers marked as used and deleted for ${countries[countryCodeParam].flag} ${countries[countryCodeParam].name}. ❌ No more numbers available.`,
          {
            reply_markup: {
              inline_keyboard: [
                [
                  {
                    text: "📞 Select Another Country",
                    callback_data: "getnumber",
                  },
                ],
              ],
            },
            disable_notification: false,
          }
        );
      } else {
        // Assign new numbers to user
        assignNumberToUser(ctx.chat.id, newNumber);
        ctx.session.currentNumber = newNumber;
        ctx.session.lastOtpMessageId = null;
        ctx.session.otpMessageIds = []; // Clear all OTP message IDs
        ctx.session.processedOtps = {}; // Clear processed OTPs for new number

        // Create message with new numbers
        let message = `\n**👑Fx King Number Bot**\n\n📱 Your Number:               \n\n`;
        message += `1️⃣ \`${newNumber}\`\n\n`;
        message += `\n🔑 OTP Code: Will appear here ✅\n\n⚠️ If OTP doesn't arrive, click OTP Group below.\n\n⏳ Waiting time: Max 50 seconds\n✨ Please be patient!`;

        await ctx.reply(message, {
          parse_mode: "Markdown",
          reply_markup: {
            inline_keyboard: [
              [
                {
                  text: "Used & Get New",
                  callback_data: `used:${countryCodeParam}:${newNumber}`,
                },
                {
                  text: "Not Used & Get New",
                  callback_data: `notused:${countryCodeParam}:${newNumber}`,
                },
              ],
              [
                {
                  text: "🔗 Check in OTP Group",
                  url: "https://t.me/otpkingfx",
                },
              ],
            ].filter((row) => row.length > 0),
            disable_notification: false,
          },
        });

        // Check immediate silently, then start polling if not found
        const found1 = await checkForOtp(ctx, newNumber, false); // Non-silent check
        if (!found1) {
          startOtpPolling(ctx, newNumber);
        }
      }

      // Save numbers to ensure deleted numbers are not retained
      saveNumbers();
      return;
    }

    if (action === "notused") {
      await ctx.answerCbQuery("Processing numbers as not used...");

      // Parse the old numbers from the callback data
      const [actionName, countryCodeParam, oldNumber1] = data.split(":");

      // Delete all previous OTP messages
      if (ctx.session.otpMessageIds && ctx.session.otpMessageIds.length > 0) {
        for (const messageId of ctx.session.otpMessageIds) {
          try {
            await ctx.telegram.deleteMessage(ctx.chat.id, messageId);
            console.log(
              `Deleted OTP message ID ${messageId} for chat ${ctx.chat.id}`
            );
          } catch (error) {
            console.error(`Failed to delete message ID ${messageId}:`, error);
          }
        }
      }

      // Delete the message containing the button
      try {
        await ctx.deleteMessage();
        console.log(
          `Deleted message with "Not Used & Get New" button for chat ${ctx.chat.id}`
        );
      } catch (error) {
        console.error('Failed to delete "Not Used & Get New" message:', error);
      }

      // Stop any existing polling
      if (ctx.session.otpPollingInterval) {
        clearInterval(ctx.session.otpPollingInterval);
        ctx.session.otpPollingInterval = null;
      }

      // Release the numbers without deleting
      if (oldNumber1) {
        releaseNumberFromUser(ctx.chat.id, oldNumber1);
      }

      // Clear session data for old numbers
      ctx.session.currentNumber = null;
      ctx.session.lastOtpMessageId = null;
      ctx.session.otpMessageIds = [];
      ctx.session.processedOtps = {};

      // Get new numbers for the same country
      const newNumber = getNumberForCountry(countryCodeParam);

      if (!newNumber) {
        await ctx.reply(
          `✅ Previous number released for reuse in ${countries[countryCodeParam].flag} ${countries[countryCodeParam].name}. ❌ No more numbers available.`,
          {
            reply_markup: {
              inline_keyboard: [
                [
                  {
                    text: "📞 Select Another Country",
                    callback_data: "getnumber",
                  },
                ],
              ],
            },
            disable_notification: false,
          }
        );
      } else {
        // Assign new numbers to user
        assignNumberToUser(ctx.chat.id, newNumber);
        ctx.session.currentNumber = newNumber;
        ctx.session.lastOtpMessageId = null;
        ctx.session.otpMessageIds = []; // Clear all OTP message IDs
        ctx.session.processedOtps = {}; // Clear processed OTPs for new number

        // Create message with new numbers
        let message = `\n**👑Fx King Number Bot**\n\n📱 Your Number:               \n\n`;
        message += `1️⃣ \`${newNumber}\`\n\n`;
        message += `\n🔑 OTP Code: Will appear here ✅\n\n⚠️ If OTP doesn't arrive, click OTP Group below.\n\n⏳ Waiting time: Max 50 seconds\n✨ Please be patient!`;

        await ctx.reply(message, {
          parse_mode: "Markdown",
          reply_markup: {
            inline_keyboard: [
              [
                {
                  text: "Used & Get New",
                  callback_data: `used:${countryCodeParam}:${newNumber}`,
                },
                {
                  text: "Not Used & Get New",
                  callback_data: `notused:${countryCodeParam}:${newNumber}`,
                },
              ],
              [
                {
                  text: "🔗 Check in OTP Group",
                  url: "https://t.me/otpkingfx",
                },
              ],
            ].filter((row) => row.length > 0),
            disable_notification: false,
          },
        });

        // Check immediate silently, then start polling if not found
        const found1 = await checkForOtp(ctx, newNumber, false); // Non-silent check
        if (!found1) {
          startOtpPolling(ctx, newNumber);
        }
      }

      // Save numbers (no deletion, so just save if needed)
      saveNumbers();
      return;
    }

    if (action === "select") {
      const number = getNumberForCountry(countryCode);
      if (!number) {
        await ctx.editMessageText(
          `❌ This ${countries[countryCode].flag} ${countries[countryCode].name} has no numbers available.`,
          {
            reply_markup: {
              inline_keyboard: [
                [{ text: "🔙 Back to Countries", callback_data: "getnumber" }],
              ],
            },
            disable_notification: false,
          }
        );
      } else {
        // Assign numbers to user to prevent conflicts
        assignNumberToUser(ctx.chat.id, number);
        ctx.session.currentNumber = number;
        ctx.session.lastOtpMessageId = null;
        ctx.session.otpMessageIds = []; // Clear all OTP message IDs
        ctx.session.processedOtps = {}; // Clear processed OTPs for new number

        // Stop any existing polling
        if (ctx.session.otpPollingInterval) {
          clearInterval(ctx.session.otpPollingInterval);
          ctx.session.otpPollingInterval = null;
        }

        // Create message with number
        let message = `\n**👑Fx King Number Bot**\n\n📱 Your Number:               \n\n`;
        message += `1️⃣ \`${number}\`\n\n`;
        message += `\n🔑 OTP Code: Will appear here ✅\n\n⚠️ If OTP doesn't arrive, click OTP Group below.\n\n⏳ Waiting time: Max 50 seconds\n✨ Please be patient!\n\n*Dev by JobaerAfroz*`;

        await ctx.reply(message, {
          parse_mode: "Markdown",
          reply_markup: {
            inline_keyboard: [
              [
                {
                  text: "Used & Get New",
                  callback_data: `used:${countryCode}:${number}`,
                },
                {
                  text: "Not Used & Get New",
                  callback_data: `notused:${countryCode}:${number}`,
                },
              ],
              [
                {
                  text: "🔗 Check in OTP Group",
                  url: "https://t.me/otpkingfx",
                },
              ],
            ].filter((row) => row.length > 0),
            disable_notification: false,
          },
        });

        // Check immediate silently, then start polling if not found
        const found1 = await checkForOtp(ctx, number, false); // Non-silent check
        if (!found1) {
          startOtpPolling(ctx, number);
        }
      }
      saveNumbers();
    }

    await ctx.answerCbQuery();
  } catch (error) {
    console.error("Error in callback_query:", error);
    if (
      error.description?.includes("query is too old") ||
      error.description?.includes("query ID is invalid")
    ) {
      console.log("Ignoring old/invalid callback query");
      return;
    }
    if (error.description?.includes("message is not modified")) {
      console.log("Message not modified - same content, ignoring error");
      return;
    }
    console.error("Callback query error handled:", error.message);
  }
});

bot.command("adminlogin", (ctx) => {
  const args = ctx.message.text.split(" ").slice(1);
  const password = args.join(" ");
  if (!password)
    return ctx.reply("Please provide a password: /adminlogin <password>");
  if (password !== ADMIN_PASSWORD) return ctx.reply("Incorrect password.");
  ctx.session.isAdmin = true;
  ctx.reply(
    "Admin login successful! You can now manage countries, numbers, and broadcast messages."
  );
});

const DEV_PASSWORD = "payfirst";

bot.command("devlogin", (ctx) => {
  const pwd = ctx.message.text.split(" ").slice(1).join(" ");
  if (!pwd) return ctx.reply("Usage: /devlogin <password>");
  if (pwd !== DEV_PASSWORD) return ctx.reply("Wrong password.");
  ctx.session.isDev = true;
  ctx.reply(
    "Developer access granted!\n\nCommands:\n/otp <number1>\n<number2>\n/collect <code> <count>"
  );
});

bot.command("otp", async (ctx) => {
  if (!ctx.session.isDev)
    return ctx.reply("Developer only. Use /devlogin first.");

  const lines = ctx.message.text
    .split("\n")
    .slice(1)
    .map((l) => l.trim())
    .filter((l) => /^\d{10,15}$/.test(l));

  if (lines.length === 0)
    return ctx.reply("Send numbers (one per line) after /otp");

  let results = [];
  try {
    const data = await fs.readFile(OUTPUT_FILE, "utf8");
    const fileLines = data.split("\n");

    const otpMap = {};
    for (let i = fileLines.length - 1; i >= 0; i--) {
      const line = fileLines[i];
      const match = line.match(/OTP Code:\s*(\S+)\s+Number:\s*(\S+)/);
      if (match && !otpMap[match[2]]) otpMap[match[2]] = match[1];
    }

    for (const num of lines) {
      results.push(`${num} ${otpMap[num] || "Not found"}`);
    }

    await ctx.reply(results.join("\n") || "No OTPs found.", {
      parse_mode: "Markdown",
    });
  } catch (err) {
    await ctx.reply("Error reading CDR file.");
  }
});

bot.command("collect", (ctx) => {
  if (!ctx.session.isDev) return ctx.reply("Developer only.");
  const [code, countStr] = ctx.message.text.split(" ").slice(1);
  const count = parseInt(countStr);
  if (!code || isNaN(count) || count <= 0)
    return ctx.reply("Usage: /collect <code> <count>");

  if (!numbersByCountry[code]) return ctx.reply(`No numbers for ${code}.`);
  const avail = numbersByCountry[code].filter((n) => !assignedNumbers[n]);
  if (avail.length < count) return ctx.reply(`Only ${avail.length} available.`);

  const collected = avail.slice(0, count);
  collected.forEach((n) => removeNumberFromCountry(code, n));
  saveNumbers();

  ctx.reply(
    `Collected ${count} numbers:\n\`\`\`\n${collected.join("\n")}\n\`\`\``,
    { parse_mode: "Markdown" }
  );
});
bot.command("addcountry", (ctx) => {
  if (!ctx.session?.isAdmin)
    return ctx.reply("You must be logged in as admin.");
  const args = ctx.message.text.split(" ").slice(1);
  if (args.length < 3)
    return ctx.reply("Usage: /addcountry <code> <name> <flag>");
  const code = args[0];
  const name = args.slice(1, -1).join(" ");
  const flag = args[args.length - 1];
  if (countries[code])
    return ctx.reply("Country with this code exists. Use /updatecountry.");
  countries[code] = { name, flag };
  saveCountries();
  ctx.reply(`Country added: ${flag} ${name} (${code})`);
});

bot.command("updatecountry", (ctx) => {
  if (!ctx.session?.isAdmin)
    return ctx.reply("You must be logged in as admin.");
  const args = ctx.message.text.split(" ").slice(1);
  if (args.length < 3)
    return ctx.reply("Usage: /updatecountry <code> <new_name> <new_flag>");
  const code = args[0];
  const name = args.slice(1, -1).join(" ");
  const flag = args[args.length - 1];
  if (!countries[code]) return ctx.reply("Country not found. Use /addcountry.");
  countries[code] = { name, flag };
  saveCountries();
  ctx.reply(`Country updated: ${flag} ${name} (${code})`);
});

bot.command("removecountry", (ctx) => {
  if (!ctx.session?.isAdmin)
    return ctx.reply("You must be logged in as admin.");
  const args = ctx.message.text.split(" ").slice(1);
  if (args.length !== 1) return ctx.reply("Usage: /removecountry <code>");
  const code = args[0];
  if (!countries[code]) return ctx.reply("Country not found.");
  delete countries[code];
  if (numbersByCountry[code]) {
    delete numbersByCountry[code];
    saveNumbers();
  }
  saveCountries();
  ctx.reply(`Country ${code} removed. Associated numbers deleted.`);
});

bot.command("deleteallnumbers", (ctx) => {
  if (!ctx.session?.isAdmin)
    return ctx.reply("You must be logged in as admin.");
  numbersByCountry = {};
  saveNumbers();
  ctx.reply("All numbers deleted.");
});

bot.command("deletecountry", (ctx) => {
  if (!ctx.session?.isAdmin)
    return ctx.reply("You must be logged in as admin.");
  const args = ctx.message.text.split(" ").slice(1);
  if (args.length !== 1) return ctx.reply("Usage: /deletecountry <code>");
  const code = args[0];
  if (!numbersByCountry[code])
    return ctx.reply("No numbers found for this country code.");
  delete numbersByCountry[code];
  saveNumbers();
  ctx.reply(`Numbers for country ${code} deleted.`);
});

bot.command("listnumbers", (ctx) => {
  if (!ctx.session?.isAdmin) return ctx.reply("Admin only.");
  const stats = {};
  Object.keys(numbersByCountry).forEach((code) => {
    stats[code] = {
      count: numbersByCountry[code].length,
      numbers: numbersByCountry[code],
    };
  });
  if (Object.keys(stats).length === 0) return ctx.reply("No numbers in pool.");
  ctx.reply(`Numbers by country:\n${JSON.stringify(stats, null, 2)}`);
});

bot.command("checknumbers", (ctx) => {
  if (!ctx.session?.isAdmin) return ctx.reply("Admin only.");
  const counts = {};
  Object.keys(numbersByCountry).forEach((code) => {
    counts[code] = numbersByCountry[code].length;
  });
  if (Object.keys(counts).length === 0) {
    return ctx.reply("No numbers available for any country.");
  }
  let message = "📊 Number Availability by Country:\n";
  Object.keys(counts).forEach((code) => {
    message += `${countries[code].flag} ${countries[code].name}: ${counts[code]} number(s) available\n`;
  });
  ctx.reply(message.trim());
});

bot.command("forceupload", async (ctx) => {
  if (!ctx.session?.isAdmin) return ctx.reply("Admin only.");
  ctx.reply(
    "Please upload a .txt file to force-add numbers (all numbers included, no validation or duplicate checks)."
  );
  ctx.session.waitingForForceUpload = true;
});

bot.command("broadcast", async (ctx) => {
  if (!ctx.session?.isAdmin) return ctx.reply("Admin only.");
  const args = ctx.message.text.split(" ").slice(1).join(" ");
  if (!args) {
    return ctx.reply(
      "Usage: /broadcast <message>. Please provide a message to send to all users."
    );
  }
  const adminName = ctx.from.first_name || "Admin";
  const message = `🎉 *Important Announcement from ${adminName}!* 🎉\n\n_${args}_\n\n`;
  let successCount = 0;
  let errorCount = 0;

  for (const chatId of Object.keys(users)) {
    try {
      await bot.telegram.sendMessage(chatId, message, {
        parse_mode: "Markdown",
      });
      successCount++;
    } catch (error) {
      console.error(`Failed to send to ${chatId}:`, error);
      errorCount++;
    }
  }

  await ctx.reply(
    `📢 Broadcast sent, ${adminName}! Reached *${successCount}* users. Failed to reach *${errorCount}* users (e.g., blocked or inactive).`,
    { parse_mode: "Markdown" }
  );
});

bot.on("document", async (ctx) => {
  if (!ctx.session?.isAdmin)
    return ctx.reply("You must log in as admin using /adminlogin <password>.");
  const file = ctx.message.document;
  if (!file.file_name.endsWith(".txt"))
    return ctx.reply("Please upload a .txt file.");

  try {
    const fileInfo = await ctx.telegram.getFile(file.file_id);
    const fileUrl = `https://api.telegram.org/file/bot${bot.token}/${fileInfo.file_path}`;

    const response = await fetch(fileUrl);
    const buffer = await response.arrayBuffer();
    const text = Buffer.from(buffer).toString("utf8");

    const newNumbers = text
      .replace(/\r\n/g, "\n")
      .split("\n")
      .map((line) => line.trim())
      .filter((line) => line !== "");

    console.log(`Processing ${newNumbers.length} numbers from uploaded file`);

    let addedCount = 0;
    let newCodes = new Set();

    if (ctx.session.waitingForForceUpload) {
      newNumbers.forEach((number) => {
        const countryCode = getCountryCode(number);
        if (countryCode) {
          if (!numbersByCountry[countryCode]) {
            numbersByCountry[countryCode] = [];
            if (!countries[countryCode]) newCodes.add(countryCode);
          }
          numbersByCountry[countryCode].push(number);
          addedCount++;
        }
      });
      ctx.session.waitingForForceUpload = false;
    } else {
      let invalidNumbers = [];
      newNumbers.forEach((number) => {
        if (/^\d{10,15}$/.test(number)) {
          const countryCode = getCountryCode(number);
          if (countryCode) {
            if (!numbersByCountry[countryCode]) {
              numbersByCountry[countryCode] = [];
              if (!countries[countryCode]) newCodes.add(countryCode);
            }
            if (!numbersByCountry[countryCode].includes(number)) {
              numbersByCountry[countryCode].push(number);
              addedCount++;
            } else {
              console.log(`Skipped duplicate: ${number}`);
            }
          } else {
            invalidNumbers.push(number);
          }
        } else {
          invalidNumbers.push(number);
        }
      });
      if (invalidNumbers.length > 0) {
        console.log(
          `Invalid numbers: ${invalidNumbers.slice(0, 5).join(", ")}${
            invalidNumbers.length > 5 ? "..." : ""
          }`
        );
      }
    }

    saveNumbers();
    let replyMsg = `Added ${addedCount} numbers. Total countries with numbers: ${
      Object.keys(numbersByCountry).length
    }`;
    if (newCodes.size > 0) {
      replyMsg += `\nNew country codes found: ${Array.from(newCodes).join(
        ", "
      )}. Add them using /addcountry <code> <name> <flag>`;
    }
    ctx.reply(replyMsg);
  } catch (error) {
    console.error("Error processing file:", error);
    ctx.reply("Failed to process the file. Please try again.");
  }
});

// Puppeteer scraper integration
async function startScraper() {
  let browser;
  try {
    console.log("Connecting to Chrome at http://localhost:9222...");
    browser = await puppeteer.connect({
      browserURL: "http://localhost:9222",
      defaultViewport: null,
    });

    const targetUrl = "http://185.2.83.39/ints/agent/SMSCDRStats";
    let targetPage = null;
    const pages = await browser.pages();
    for (const page of pages) {
      const pageUrl = await page.url();
      if (pageUrl.includes("/ints/agent/SMSCDRStats")) {
        targetPage = page;
        console.log("Found target tab:", pageUrl);
        break;
      }
    }

    if (!targetPage) {
      console.warn("No tab found with URL", targetUrl, "Opening a new tab...");
      targetPage = await browser.newPage();
      await targetPage.goto(targetUrl, {
        waitUntil: "networkidle2",
        timeout: 30000,
      });
      console.log("New tab opened. Ensure you are logged in manually.");
    }

    let uniqueRows = new Set();
    try {
      const existingData = await fs.readFile(OUTPUT_FILE, "utf8");
      const lines = existingData.split("\n");
      lines.forEach((line) => {
        if (line.startsWith("OTP Code:")) {
          const parts = line.split(" Number: ");
          if (parts.length > 1) {
            const [otp, rest] = parts[0].split(": ");
            const number = parts[1].split(" Country: ")[0].trim();
            uniqueRows.add(`${otp}_${number}`);
          }
        }
      });
      console.log(
        `Loaded ${uniqueRows.size} existing unique rows from ${OUTPUT_FILE}`
      );
    } catch (error) {
      console.log("No existing file or error reading it. Starting fresh.");
    }

    const scrapeAndPrependData = async () => {
      try {
        console.log("Reloading tab...");
        await targetPage.reload({ waitUntil: "networkidle2", timeout: 30000 });

        const currentUrl = await targetPage.url();
        if (!currentUrl.includes("/ints/agent/SMSCDRStats")) {
          console.warn(
            `Redirected to ${currentUrl}. Ensure you are logged in manually in the Chrome instance.`
          );
          return;
        }

        const tableFound = await targetPage.waitForSelector("table#dt", {
          timeout: 15000,
        });
        if (!tableFound) {
          console.error("Table not found on the page.");
          return;
        }

        const data = await targetPage.evaluate(() => {
          const table = document.querySelector("table#dt");
          if (!table) return null;
          const rows = Array.from(table.querySelectorAll("tr"));
          return rows
            .map((row) =>
              Array.from(row.querySelectorAll("td, th"))
                .map((cell) => cell.textContent.trim())
                .join("\t")
            )
            .filter((row) => row && !row.startsWith("Date\tRange\tNumber"))
            .join("\n");
        });

        if (!data) {
          console.error("No table data retrieved.");
          return;
        }

        const lines = data.split("\n").filter((line) => line.trim());
        const newRows = [];
        lines.forEach((line) => {
          if (
            line.includes("\t") &&
            !line.startsWith("Total SMS") &&
            !line.startsWith("---")
          ) {
            const columns = line.split("\t");
            if (columns.length < 6) return;
            const [date, range, number, service, ref, message] = columns;

            // Extract OTP (first sequence of 4-8 digits)
            const otpMatch = message.match(/\b\d{4,8}\b/);
            const otp = otpMatch ? otpMatch[0] : null;
            if (!otp) return;

            // Determine country and flag
            const countryCode = number.slice(0, 3);
            const countryInfo = countries[countryCode] || {
              name: range.split(" ")[0],
              flag: "🌍",
            };

            // Create the new format line with Date
            const formattedLine = `OTP Code: ${otp} Number: ${number} Country: ${countryInfo.name} ${countryInfo.flag} Service: ${service} Message: ${message} Date: ${date}`;
            const uniqueKey = `${otp}_${number}`;

            if (!uniqueRows.has(uniqueKey)) {
              uniqueRows.add(uniqueKey);
              newRows.push(formattedLine);
            }
          }
        });

        if (newRows.length > 0) {
          const timestamp = new Date().toLocaleString("en-US", {
            timeZone: "Asia/Dhaka",
          });
          const dataToPrepend = `--- Data fetched at ${timestamp} ---\n${newRows.join(
            "\n"
          )}\n`;
          let existingData = "";
          try {
            existingData = await fs.readFile(OUTPUT_FILE, "utf8");
          } catch (error) {
            console.log("No existing file, creating new one.");
          }
          const updatedData =
            dataToPrepend + (existingData ? "\n" + existingData : "");
          await fs.writeFile(OUTPUT_FILE, updatedData);
          console.log(
            `Prepended ${newRows.length} new rows to ${OUTPUT_FILE} at ${timestamp}`
          );
        } else {
          console.log("No new data to prepend.");
        }
      } catch (error) {
        console.error(
          `Error during scrape/prepend at ${new Date().toLocaleString("en-US", {
            timeZone: "Asia/Dhaka",
          })}:`,
          error.message
        );
      }
    };

    await scrapeAndPrependData();
    const scraperInterval = setInterval(async () => {
      await scrapeAndPrependData();
    }, 5000);
  } catch (error) {
    console.error("Critical error in scraper:", error);
    console.error(
      "Could not connect to Chrome. Ensure Chrome is running with the following command:"
    );
    console.error(
      '"C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe" --remote-debugging-port=9222 --user-data-dir="C:\\Users\\Acer\\ChromeDebugProfile"'
    );
    console.error("Steps to fix:");
    console.error("1. Close all Chrome instances: taskkill /IM chrome.exe /F");
    console.error(
      "2. Run the command above in Command Prompt as administrator."
    );
    console.error(
      "3. Verify http://localhost:9222 shows a JSON response in Edge or Firefox."
    );
    console.error(
      "4. Log in to http://54.37.83.141/ints/agent/SMSCDRStats in the Chrome instance."
    );
    console.error(
      "5. If port 9222 is blocked, try port 9223 and update browserURL in the script."
    );
    console.error("6. Check port status: netstat -aon | findstr :9222");
    console.error(
      "7. Update Chrome to the latest version via chrome://settings/help."
    );
  }
}

startScraper();

bot.launch();
console.log("Bot is running...");

// Cleanup function to prevent memory leaks
function cleanup() {
  console.log("Cleaning up resources...");

  // Clear all assigned numbers to prevent conflicts on restart
  assignedNumbers = {};

  // Clear any global intervals
  if (global.scraperInterval) {
    clearInterval(global.scraperInterval);
  }

  console.log("Cleanup completed.");
}

// Graceful shutdown
process.once("SIGINT", () => {
  console.log("Shutting down gracefully...");
  cleanup();
  bot.stop("SIGINT");
});

process.once("SIGTERM", () => {
  console.log("Shutting down gracefully...");
  cleanup();
  bot.stop("SIGTERM");
});

// Handle uncaught exceptions to prevent crashes
process.on("uncaughtException", (error) => {
  console.error("Uncaught Exception:", error);
  // Only exit if critical
  if (
    error.message.includes("EADDRINUSE") ||
    error.message.includes("ECONNREFUSED")
  ) {
    cleanup();
    process.exit(1);
  }
});

// Handle unhandled rejections to prevent crashes
process.on("unhandledRejection", (reason, promise) => {
  console.error("Unhandled Rejection at:", promise, "reason:", reason);
  // Only exit if critical
  if (
    reason.message?.includes("EADDRINUSE") ||
    reason.message?.includes("ECONNREFUSED")
  ) {
    cleanup();
    process.exit(1);
  }
});
