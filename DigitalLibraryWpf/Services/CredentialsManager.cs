using System;
using System.IO;
using System.Security.Cryptography;
using System.Text;
using System.Text.Json;
using DigitalLibraryWpf.Models; // Assuming StoredCredentials will be defined here or in its own file

namespace DigitalLibraryWpf.Services
{
    internal class StoredCredentials
    {
        public string? Username { get; set; }
        public string? EncryptedPassword { get; set; } // Base64 string of encrypted bytes
        public bool RememberMe { get; set; }
    }

    public class CredentialsManager
    {
        private static readonly string AppName = "DigitalLibraryWpf";
        private static readonly string FileName = "user.dat";
        private static readonly byte[] s_entropy = new byte[] { 19, 84, 121, 9, 4, 77, 113, 201, 33, 98, 62, 7, 25, 199, 53, 10 }; // Just some arbitrary bytes

        private static string GetCredentialsFilePath()
        {
            string appDataPath = Environment.GetFolderPath(Environment.SpecialFolder.LocalApplicationData);
            string appFolderPath = Path.Combine(appDataPath, AppName);
            Directory.CreateDirectory(appFolderPath); // Ensure directory exists
            return Path.Combine(appFolderPath, FileName);
        }

        public static void SaveCredentials(string username, string password, bool rememberMe)
        {
            try
            {
                byte[] passwordBytes = Encoding.UTF8.GetBytes(password);
                byte[] encryptedPasswordBytes = ProtectedData.Protect(passwordBytes, s_entropy, DataProtectionScope.CurrentUser);
                string encryptedPasswordBase64 = Convert.ToBase64String(encryptedPasswordBytes);

                var credentials = new StoredCredentials
                {
                    Username = username,
                    EncryptedPassword = encryptedPasswordBase64,
                    RememberMe = rememberMe
                };

                string json = JsonSerializer.Serialize(credentials);
                File.WriteAllText(GetCredentialsFilePath(), json);
            }
            catch (Exception ex)
            {
                // Log error or handle appropriately
                Console.WriteLine($"Error saving credentials: {ex.Message}");
            }
        }

        public static (string? Username, string? Password, bool RememberMe) LoadCredentials()
        {
            string filePath = GetCredentialsFilePath();
            if (!File.Exists(filePath))
            {
                return (null, null, false);
            }

            try
            {
                string json = File.ReadAllText(filePath);
                var credentials = JsonSerializer.Deserialize<StoredCredentials>(json);

                if (credentials == null || string.IsNullOrEmpty(credentials.EncryptedPassword))
                {
                    return (credentials?.Username, null, credentials?.RememberMe ?? false);
                }

                byte[] encryptedPasswordBytes = Convert.FromBase64String(credentials.EncryptedPassword);
                byte[] passwordBytes = ProtectedData.Unprotect(encryptedPasswordBytes, s_entropy, DataProtectionScope.CurrentUser);
                string password = Encoding.UTF8.GetString(passwordBytes);

                return (credentials.Username, password, credentials.RememberMe);
            }
            catch (Exception ex)
            {
                // Log error or handle appropriately (e.g., corrupted file)
                Console.WriteLine($"Error loading credentials: {ex.Message}");
                ClearCredentials(); // If file is corrupt, clear it
                return (null, null, false);
            }
        }

        public static void ClearCredentials()
        {
            try
            {
                string filePath = GetCredentialsFilePath();
                if (File.Exists(filePath))
                {
                    File.Delete(filePath);
                }
            }
            catch (Exception ex)
            {
                // Log error or handle appropriately
                Console.WriteLine($"Error clearing credentials: {ex.Message}");
            }
        }
    }
}
